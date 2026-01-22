# -*- coding: utf-8 -*-

import pandas as pd
import geopandas as gpd
import numpy as np
from dateutil import parser
from shapely.geometry import LineString, MultiPoint
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox, QPushButton, QMessageBox, QGroupBox
from qgis.PyQt.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class UeberlappungFilter:
    """Class for filtering point data based on overlapping paths."""
    
    def __init__(self, layer, parent_dialog):
        """Initialize the overlap filter with a vector layer."""
        self.layer = layer
        self.parent_dialog = parent_dialog
        self.gdf = None
        self.timestamp_field = None
        self.max_timedelta = None
        self.working_width = None
        self.tolerance = None
        self.filter_column = None
        self.filtered_ids = []
        self.path_break_attribute = None  # Additional attribute for path separation
        self.path_break_threshold = None  # Threshold value for path separation
        
    def prepare_data(self):
        # Convert QGIS layer to GeoDataFrame
        features = [feat for feat in self.layer.getFeatures()]
        
        # Create GeoDataFrame
        self.gdf = gpd.GeoDataFrame.from_features(features)
        
        # Add x and y coordinates
        self.gdf["x"] = self.gdf.geometry.x
        self.gdf["y"] = self.gdf.geometry.y
        
        return True
    
    def process_timestamps(self):
        if not self.timestamp_field or not self.max_timedelta:
            return False
            
        # Convert timestamps to unix timestamps
        self.gdf['unix_timestamp'] = self.gdf.apply(
            lambda row: self._convert_to_unix_timestamp(row), 
            axis=1
        )
        
        # Check if timestamp conversion was successful
        if self.gdf['unix_timestamp'].isna().all():
            self.parent_dialog.log.log_event("Überlappung", {"Fehler": "Keine gültigen Zeitstempel gefunden. Bitte überprüfen Sie das Zeitstempelformat."})
            return False
        
        # Create Duration column
        self.gdf['Duration'] = None
        
        # Calculate time delta between points, handling None values
        for u in range(1, len(self.gdf)):
            if pd.notna(self.gdf.loc[u, 'unix_timestamp']) and pd.notna(self.gdf.loc[u - 1, 'unix_timestamp']):
                self.gdf.loc[u, 'Duration'] = self.gdf.loc[u, 'unix_timestamp'] - self.gdf.loc[u - 1, 'unix_timestamp']
            else:
                # Use a default value if timestamps are missing
                self.gdf.loc[u, 'Duration'] = self.max_timedelta + 1 
        
        # Calculate median time delta (ignoring NaN values)
        valid_durations = self.gdf['Duration'].dropna()
        if len(valid_durations) > 0:
            median_duration = valid_durations.median()
        else:
            # If no valid durations, use a default value
            median_duration = self.max_timedelta
            self.parent_dialog.log.log_event("Überlappung", {"Warnung": "Keine gültigen Zeitdifferenzen gefunden. Verwende Standardwert."})
        
        # Handle None values in Duration column
        none_count = self.gdf['Duration'].isna().sum()
        if none_count > 0:
            self.gdf['Duration'].fillna(median_duration, inplace=True)
        
        # Calculate cutoff for path separation
        cut_off = self.max_timedelta + median_duration
        
        # Generate path numbers
        nr = 1
        self.gdf['Path'] = None
        
        # Check if additional attribute for path breaks is specified
        has_attr_break = self.path_break_attribute is not None and \
                        self.path_break_threshold is not None and \
                        self.path_break_attribute in self.gdf.columns
        
        # If additional attribute is specified, create a column for attribute changes
        if has_attr_break:
            self.gdf['attr_change'] = 0
            for i in range(1, len(self.gdf)):
                try:
                    current_val = float(self.gdf.loc[i, self.path_break_attribute])
                    prev_val = float(self.gdf.loc[i-1, self.path_break_attribute])
                    # Mark significant changes in the attribute
                    if abs(current_val - prev_val) > self.path_break_threshold:
                        self.gdf.loc[i, 'attr_change'] = 1
                except (ValueError, TypeError):
                    pass
        
        # Assign path numbers based on time gaps and attribute changes
        for v in range(len(self.gdf)):
            # First point always starts a new path
            if v == 0:
                self.gdf.loc[v, 'Path'] = nr
                continue
                
            # Check for time gap
            time_break = self.gdf.loc[v, 'Duration'] > cut_off
            
            # Check for attribute break
            attr_break = has_attr_break and self.gdf.loc[v, 'attr_change'] == 1
            
            # Start a new path if either condition is met
            if time_break or attr_break:
                nr += 1
            
            self.gdf.loc[v, 'Path'] = nr
        
        return True
    
    def _convert_to_unix_timestamp(self, row):
        """Convert timestamp string to unix timestamp."""
        try:
            # Handle empty or None values
            if pd.isna(row[self.timestamp_field]) or str(row[self.timestamp_field]).strip() == '':
                return None
                
            # Get the timestamp string
            timestamp_str = str(row[self.timestamp_field])
            
            # Special handling for "01.01.0000 12:18:56.0000" format
            if '01.01.0000' in timestamp_str:
                # Extract just the time part and use a reference date
                time_part = timestamp_str.split(' ')[1]
                from datetime import datetime
                # Use current date with the time from the timestamp
                reference_date = datetime.now().strftime('%Y-%m-%d')
                timestamp_str = f"{reference_date} {time_part}"
                try:
                    parsed_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    # Use sequential timestamps based on row index to preserve order
                    return int(parsed_date.timestamp()) + row.name  # Add row index to ensure unique timestamps
                except ValueError:
                    pass
            
            # Try to parse as ISO format
            try:
                parsed_date = parser.parse(timestamp_str)
                unix_timestamp = int(parsed_date.timestamp())
                return unix_timestamp
            except Exception:
                # Try common formats
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y/%m/%d %H:%M:%S',
                    '%d.%m.%Y %H:%M:%S',
                    '%m/%d/%Y %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y%m%d%H%M%S',
                    '%d.%m.%Y %H:%M:%S.%f'  # Format with milliseconds
                ]
                
                for fmt in formats:
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(timestamp_str, fmt)
                        unix_timestamp = int(parsed_date.timestamp())
                        return unix_timestamp
                    except ValueError:
                        continue
                
                # If all else fails, use row index as timestamp to preserve order
                return int(datetime.now().timestamp()) + row.name
                
        except Exception as e:
            self.parent_dialog.log.log_event("Überlappung", 
                {"Fehler": f"Fehler beim Parsen des Zeitstempels: {e}"}
            )
            # Use row index as timestamp to preserve order
            from datetime import datetime
            return int(datetime.now().timestamp()) + row.name
    
    def detect_overlaps(self):
        if not self.working_width or not self.tolerance:
            return False
            
        try:
            # Get all path numbers
            path_numbers = self.gdf.Path.unique()
            
            # Check if Path column has valid values
            if pd.isna(path_numbers).all():
                self.parent_dialog.log.log_event("Überlappung", {"Fehler": "Keine gültigen Pfadnummern gefunden."})
                return False
            
            # Column to identify path numbers to ignore (single points)
            self.gdf['Path_ignore'] = 0
            
            # Identify paths with only one point
            for i in range(len(path_numbers)):
                if pd.notna(path_numbers[i]) and sum(self.gdf.Path == path_numbers[i]) < 2:
                    self.gdf.loc[self.gdf['Path'] == path_numbers[i], 'Path_ignore'] = 1
            
            # Create DataFrame only containing paths with more than one point
            paths_for_lines = self.gdf.drop(self.gdf[self.gdf['Path_ignore'] == 1].index)
            
            # Check if we have any valid paths
            if paths_for_lines.empty:
                self.parent_dialog.log.log_event("Überlappung", {"Warnung": "Keine gültigen Pfade mit mehreren Punkten gefunden."})
                # No overlaps to detect
                self.filtered_ids = []
                return True
            
            # Create lines from points
            try:
                lines = paths_for_lines.groupby('Path')['geometry'].apply(lambda x: LineString(x.tolist()))
                lines = gpd.GeoDataFrame(lines, geometry='geometry')
            except Exception as e:
                self.parent_dialog.log.log_event("Überlappung", {"Fehler": f"Fehler beim Erstellen der Linien: {e}"})
                return False
            
            # Add start and stop time to the lines
            lines['StartTime'] = paths_for_lines.groupby(['Path'])['unix_timestamp'].min()
            lines['StopTime'] = paths_for_lines.groupby(['Path'])['unix_timestamp'].max()
            
            # Define coordinate system
            lines = lines.set_crs(self.layer.crs().toWkt())
            
            # Add single point paths back to the lines DataFrame
            single_points = self.gdf[self.gdf['Path_ignore'] == 1]
            if not single_points.empty:
                try:
                    single_point_geoms = single_points.groupby('Path')['geometry'].apply(lambda x: MultiPoint(x.tolist()))
                    single_point_geoms = gpd.GeoDataFrame(single_point_geoms, geometry='geometry')
                    
                    single_point_geoms['StartTime'] = single_points.groupby(['Path'])['unix_timestamp'].min()
                    single_point_geoms['StopTime'] = single_points.groupby(['Path'])['unix_timestamp'].max()
                    
                    single_point_geoms = single_point_geoms.set_crs(self.layer.crs().toWkt())
                    
                    lines = pd.concat([lines, single_point_geoms])
                except Exception as e:
                    self.parent_dialog.log.log_event("Überlappung", {"Warnung": f"Fehler beim Verarbeiten einzelner Punkte: {e}"})
            
            # Calculate min distances between points and lines
            self.gdf['min_distance'] = None
            for i in range(len(self.gdf)):
                if pd.isna(self.gdf.loc[i, 'unix_timestamp']):
                    continue
                    
                # Filter for lines that are before in time of current point
                filter_lines = lines[(lines['StartTime'] < self.gdf.loc[i, 'unix_timestamp']) & 
                                    (lines['StopTime'] < self.gdf.loc[i, 'unix_timestamp'])]
                
                # Calculate min distance to the remaining lines
                if not filter_lines.empty:
                    try:
                        self.gdf.loc[i, 'min_distance'] = filter_lines.distance(self.gdf.loc[i, 'geometry']).min()
                    except Exception as e:
                        self.parent_dialog.log.log_event("Überlappung", 
                            {"Warnung": f"Fehler bei der Distanzberechnung für Punkt {i}: {e}"})
            
            # Flag points for overlap
            self.gdf['Filter_overlap'] = 0
            for i in range(len(self.gdf)):
                if pd.notna(self.gdf.loc[i, 'min_distance']) and self.gdf.loc[i, 'min_distance'] < (self.working_width - self.tolerance):
                    self.gdf.loc[i, 'Filter_overlap'] = 1
            
            # Store IDs of points to filter
            self.filtered_ids = self.gdf[self.gdf['Filter_overlap'] == 1].index.tolist()
            
            return True
            
        except Exception as e:
            self.parent_dialog.log.log_event("Überlappung", {"Fehler": f"Unerwarteter Fehler bei der Überlappungserkennung: {e}"})
            return False
    
    def filter_zero_values(self, column):
        if column == "Kein Null-Wert-Filter" or column not in self.gdf.columns:
            return False
            
        self.filter_column = column
        filter_column_name = f"Filter_Zero_{column}"
        
        # Add column for flags
        self.gdf[filter_column_name] = 0
        
        # Add flags for zero values
        for i in range(len(self.gdf)):
            try:
                value = self.gdf.loc[i, column]
                # Check for zero or very close to zero (floating point comparison)
                if pd.notna(value) and abs(float(value)) < 0.0001:
                    self.gdf.loc[i, filter_column_name] = 1
            except (ValueError, TypeError):
                # Skip non-numeric values
                continue
        
        # Add zero-value filtered IDs to the filtered IDs list
        zero_filtered_ids = self.gdf[self.gdf[filter_column_name] == 1].index.tolist()
        self.filtered_ids.extend(zero_filtered_ids)
        self.filtered_ids = list(set(self.filtered_ids))  # Remove duplicates
        
        return True
    
    def get_filtered_ids(self):
        return self.filtered_ids
    
    def get_statistics(self):
        stats = {
            "total_points": len(self.gdf),
            "filtered_points": len(self.filtered_ids),
            "filtered_percentage": round(len(self.filtered_ids) / len(self.gdf) * 100, 2) if len(self.gdf) > 0 else 0
        }
        return stats
        
    def set_path_break_criteria(self, attribute=None, threshold=None):
        self.path_break_attribute = attribute
        self.path_break_threshold = threshold
        
    def update_path_break_criteria(self):
        if hasattr(self, 'path_break_combo') and hasattr(self, 'path_threshold_spin'):
            attribute = self.path_break_combo.currentText()
            if attribute == "Kein zusätzliches Attribut":
                attribute = None
                
            threshold = self.path_threshold_spin.value() if attribute else None
            
            self.set_path_break_criteria(attribute, threshold)
        
        # Create parameter groups with QGroupBox
        # Timestamp parameters group
        timestamp_group = QGroupBox("Zeitstempel-Parameter")
        timestamp_layout = QVBoxLayout(timestamp_group)
        
        # Timestamp selection
        timestamp_field_layout = QHBoxLayout()
        timestamp_label = QLabel("Zeitstempel-Spalte:")
        self.timestamp_combo = QComboBox()
        
        # Populate timestamp combo with field names
        has_timestamp_fields = False
        for field in self.layer.fields():
            field_name = field.name()
            # Try to identify timestamp fields by common names
            if any(keyword in field_name.lower() for keyword in ['time', 'date', 'zeit', 'datum', 'timestamp']):
                self.timestamp_combo.insertItem(0, field_name)  # Add at the beginning
                has_timestamp_fields = True
            else:
                self.timestamp_combo.addItem(field_name)  # Add at the end
        
        # Select the first item if we found timestamp fields
        if has_timestamp_fields:
            self.timestamp_combo.setCurrentIndex(0)
        
        timestamp_field_layout.addWidget(timestamp_label)
        timestamp_field_layout.addWidget(self.timestamp_combo)
        timestamp_layout.addLayout(timestamp_field_layout)
        
        # Max timedelta
        timedelta_layout = QHBoxLayout()
        timedelta_label = QLabel("Max. Zeitdifferenz für Pfaderkennung (Sekunden):")
        self.timedelta_spin = QDoubleSpinBox()
        self.timedelta_spin.setRange(0, 1000)
        self.timedelta_spin.setValue(5)
        self.timedelta_spin.setSingleStep(1)
        
        timedelta_layout.addWidget(timedelta_label)
        timedelta_layout.addWidget(self.timedelta_spin)
        timestamp_layout.addLayout(timedelta_layout)
        
        # Path break attribute (Issue 15)
        path_break_layout = QHBoxLayout()
        path_break_label = QLabel("Zusätzliches Attribut für Fahrspur-Unterbrechung:")
        self.path_break_combo = QComboBox()
        
        # Add empty option
        self.path_break_combo.addItem("Kein zusätzliches Attribut")
        
        # Populate with numeric field names
        for field in self.layer.fields():
            if field.isNumeric():
                field_name = field.name()
                # Try to identify workstate fields by common names
                if any(keyword in field_name.lower() for keyword in ['workstate', 'state', 'status', 'position', 'hubwerk']):
                    self.path_break_combo.insertItem(1, field_name)  # Add after the empty option
                else:
                    self.path_break_combo.addItem(field_name)  # Add at the end
        
        path_break_layout.addWidget(path_break_label)
        path_break_layout.addWidget(self.path_break_combo)
        timestamp_layout.addLayout(path_break_layout)
        
        # Path break threshold
        path_threshold_layout = QHBoxLayout()
        path_threshold_label = QLabel("Schwellenwert für Attributänderung:")
        self.path_threshold_spin = QDoubleSpinBox()
        self.path_threshold_spin.setRange(0, 1000)
        self.path_threshold_spin.setValue(0.5)
        self.path_threshold_spin.setSingleStep(0.1)
        
        path_threshold_layout.addWidget(path_threshold_label)
        path_threshold_layout.addWidget(self.path_threshold_spin)
        timestamp_layout.addLayout(path_threshold_layout)
        
        # Add timestamp group to main layout
        main_layout.addWidget(timestamp_group)
        
        # Spatial parameters group
        spatial_group = QGroupBox("Arbeitsbreite-Parameter")
        spatial_layout = QVBoxLayout(spatial_group)
        
        # Working width
        width_layout = QHBoxLayout()
        width_label = QLabel("Arbeitsbreite (m):")
        width_help = QLabel("(Typisch: 3-12m für Mähdrescher, 12-36m für Feldspritzen)")
        width_help.setStyleSheet("color: gray; font-size: 9pt;")
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.1, 100)
        self.width_spin.setValue(10)
        self.width_spin.setSingleStep(0.1)
        
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_spin)
        spatial_layout.addLayout(width_layout)
        spatial_layout.addWidget(width_help)
        
        # Tolerance
        tolerance_layout = QHBoxLayout()
        tolerance_label = QLabel("Toleranz (m):")
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(0, 10)
        self.tolerance_spin.setValue(0.1)
        self.tolerance_spin.setSingleStep(0.01)
        
        tolerance_layout.addWidget(tolerance_label)
        tolerance_layout.addWidget(self.tolerance_spin)
        spatial_layout.addLayout(tolerance_layout)
        
        # Add spatial group to main layout
        main_layout.addWidget(spatial_group)
        
        # Additional filters group
        additional_group = QGroupBox("Zusätzliche Filter (optional)")
        additional_layout = QVBoxLayout(additional_group)
        
        # Filter column for zero values
        zero_filter_layout = QHBoxLayout()
        zero_filter_label = QLabel("Spalte für Null-Wert-Filter:")
        self.zero_filter_combo = QComboBox()
        
        # Add empty option
        self.zero_filter_combo.addItem("Kein Null-Wert-Filter")
        
        # Populate zero filter combo with numeric field names
        has_yield_fields = False
        for field in self.layer.fields():
            if field.isNumeric():
                field_name = field.name()
                # Try to identify yield fields by common names
                if any(keyword in field_name.lower() for keyword in ['yield', 'ertrag', 'mass', 'menge']):
                    self.zero_filter_combo.insertItem(1, field_name)  # Add after the empty option
                    has_yield_fields = True
                else:
                    self.zero_filter_combo.addItem(field_name)  # Add at the end
        
        # Select the first yield field if found
        if has_yield_fields:
            self.zero_filter_combo.setCurrentIndex(1)
        
        zero_filter_layout.addWidget(zero_filter_label)
        zero_filter_layout.addWidget(self.zero_filter_combo)
        additional_layout.addLayout(zero_filter_layout)
        
        # Add help text
        help_text = QLabel(
            "<i>Der Null-Wert-Filter entfernt Punkte mit dem Wert 0 in der ausgewählten Spalte. "
            "Dies ist nützlich für Ertragsdaten, bei denen Nullwerte oft Fehler darstellen.</i>"
        )
        help_text.setTextFormat(Qt.RichText)
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: gray;")
        additional_layout.addWidget(help_text)
        
        # Add additional group to main layout
        main_layout.addWidget(additional_group)
        
        # Histogram placeholder
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)
        
        # Statistics label
        self.stats_label = QLabel("Keine Filterung durchgeführt")
        main_layout.addWidget(self.stats_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Filter anwenden")
        self.run_button.clicked.connect(self.run_filter)
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        
        # Connect path break UI elements to update method
        self.path_break_combo.currentIndexChanged.connect(self.update_path_break_criteria)
        self.path_threshold_spin.valueChanged.connect(self.update_path_break_criteria)
        
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)
    
        try:
            if not self.zero_filter_combo.currentText():
                return
                
            column = self.zero_filter_combo.currentText()
            
            # Clear the figure
            self.figure.clear()
            
            # Create two subplots
            ax1 = self.figure.add_subplot(121)
            ax2 = self.figure.add_subplot(122)
            
            # Get filtered and unfiltered data
            filtered_ids = self.filter.get_filtered_ids()
            
            # Convert to pandas Series for histogram, filtering out non-numeric values
            all_values = []
            for feat in self.layer.getFeatures():
                try:
                    value = feat[column]
                    if value is not None:
                        float_val = float(value)
                        all_values.append(float_val)
                except (ValueError, TypeError):
                    continue
            
            all_values = pd.Series(all_values)
            
            if all_values.empty:
                ax1.text(0.5, 0.5, 'Keine numerischen Daten vorhanden', 
                         horizontalalignment='center', verticalalignment='center')
                ax2.text(0.5, 0.5, 'Keine numerischen Daten vorhanden', 
                         horizontalalignment='center', verticalalignment='center')
            else:
                # Create filtered values by removing filtered IDs
                filtered_values = all_values.copy()
                if filtered_ids:
                    # This is a simplification since we can't directly map Series indices to feature IDs
                    # In a real implementation, you'd need to track which values correspond to which feature IDs
                    filtered_values = filtered_values.iloc[:-len(filtered_ids)] if len(filtered_ids) < len(all_values) else pd.Series([])
                
                # Plot histograms
                if not filtered_values.empty:
                    ax1.hist(filtered_values, bins=min(50, len(filtered_values)//2 + 1))
                    ax1.set_title('Gefilterte Daten')
                else:
                    ax1.text(0.5, 0.5, 'Alle Punkte gefiltert', 
                             horizontalalignment='center', verticalalignment='center')
                
                ax2.hist(all_values, bins=min(50, len(all_values)//2 + 1))
                ax2.set_title('Originaldaten')
            
            # Update the canvas
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            if self.log:
                self.log.log_event("Überlappung", {"Fehler": f"Fehler beim Erstellen des Histogramms: {str(e)}"})
            # Just don't show the histogram if there's an error
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Fehler beim Erstellen des Histogramms', 
                     horizontalalignment='center', verticalalignment='center')
            self.canvas.draw()