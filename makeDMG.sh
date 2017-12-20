#!/bin/bash

APP_NAME="Flacon"
VERSION=`/usr/libexec/PlistBuddy -c "print :CFBundleVersion" ${APP_NAME}.app/Contents/Info.plist`


DMG_NAME=${APP_NAME}_${VERSION}.dmg
BUNDLE_CONTENTS_DIR="${APP_NAME}.app/Contents/"
BUNDLE_BIN_DIR="${APP_NAME}.app/Contents/MacOs"
BUNDLE_LIB_DIR="${APP_NAME}.app/Contents/Frameworks"
BUNDLE_RESOURCES_DIR="${APP_NAME}.app/Contents/Resources"
BUNDLE_TRANSLATIONS_DIR="${BUNDLE_CONTENTS_DIR}/translations"

THIRD_PARTY_PROGS="faac flac lame mac metaflac mp3gain oggenc opusenc ttaenc vorbisgain wavpack wvgain wvunpack"
#=========================================



test -f ${DMG_NAME} && rm ${DMG_NAME}

./tools/create-dmg \
	--volname "${APP_NAME}" \
	--volicon "${BUNDLE_RESOURCES_DIR}/${APP_NAME}.icns" \
	--window-size 500 300 \
	--icon-size 96 \
	--icon ${APP_NAME}.app 135 102 \
	--hide-extension ${APP_NAME}.app \
	--app-drop-link 365 102 \
	${DMG_NAME} \
	${APP_NAME}.app
