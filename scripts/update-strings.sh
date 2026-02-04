#!/bin/bash
# Update Qt translation source files (.ts) for this plugin.
#
# Usage:
#   scripts/update-strings.sh de en
#
# Notes:
# - Targets QGIS 3 / PyQt5 tooling.
# - Translation files are written as i18n/OFEFilter_<locale>.ts

set -e

LOCALES=$*

# Base name for translation files. Must match the prefix used in ofe_filter.py.
PLUGIN_TS_BASENAME="OFEFilter"

# Try to locate a suitable pylupdate tool.
PYLUPDATE_BIN=""
for CANDIDATE in pylupdate5 pylupdate-qt5; do
  if command -v "$CANDIDATE" >/dev/null 2>&1; then
    PYLUPDATE_BIN="$CANDIDATE"
    break
  fi
done

if [ -z "$PYLUPDATE_BIN" ]; then
  echo "ERROR: Could not find pylupdate5 (or pylupdate-qt5) in PATH." >&2
  echo "Install Qt5 tools (often packaged as qttools5-dev-tools / pyqt5-dev-tools) or run this inside your QGIS/PyQt environment." >&2
  exit 1
fi

# Get newest .py files so we don't update strings unnecessarily

CHANGED_FILES=0
PYTHON_FILES=`find . -regex ".*\(ui\|py\)$" -type f`
for PYTHON_FILE in $PYTHON_FILES
do
  CHANGED=$(stat -c %Y $PYTHON_FILE)
  if [ ${CHANGED} -gt ${CHANGED_FILES} ]
  then
    CHANGED_FILES=${CHANGED}
  fi
done

# Qt translation stuff
# for .ts file
UPDATE=false
for LOCALE in ${LOCALES}
do
  TRANSLATION_FILE="i18n/${PLUGIN_TS_BASENAME}_${LOCALE}.ts"
  if [ ! -f ${TRANSLATION_FILE} ]
  then
    # Force translation string collection as we have a new language file
    touch ${TRANSLATION_FILE}
    UPDATE=true
    break
  fi

  MODIFICATION_TIME=$(stat -c %Y ${TRANSLATION_FILE})
  if [ ${CHANGED_FILES} -gt ${MODIFICATION_TIME} ]
  then
    # Force translation string collection as a .py file has been updated
    UPDATE=true
    break
  fi
done

if [ ${UPDATE} == true ]
# retrieve all python files
then
  echo ${PYTHON_FILES}
  # update .ts
  echo "Please provide translations by editing the translation files below:"
  for LOCALE in ${LOCALES}
  do
    echo "i18n/${PLUGIN_TS_BASENAME}_${LOCALE}.ts"
    # Note we don't use pylupdate with qt .pro file approach as it is flakey
    # about what is made available.
    "$PYLUPDATE_BIN" -noobsolete ${PYTHON_FILES} -ts i18n/${PLUGIN_TS_BASENAME}_${LOCALE}.ts
  done
else
  echo "No need to edit any translation files (.ts) because no python files"
  echo "has been updated since the last update translation. "
fi
