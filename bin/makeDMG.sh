#!/bin/bash

CREATE_DMG="create-dmg-1.0.8/bin/create-dmg"

if [ "${APP_NAME}" = "" ]; then
	echo "Missing APP_NAME argument in the spec file" >&2
	exit 1
fi

VERSION=`/usr/libexec/PlistBuddy -c "print :CFBundleVersion" ${APP_NAME}.app/Contents/Info.plist`
DMG_NAME=${APP_NAME}_${VERSION}.dmg
BUNDLE_RESOURCES_DIR="${APP_NAME}.app/Contents/Resources"


test -f ${DMG_NAME} && rm ${DMG_NAME}

PATH=${PATH}:$(dirname "$BASH_SOURCE")

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
${DIR}/${CREATE_DMG} \
	--volname "${APP_NAME}" \
	--volicon "${BUNDLE_RESOURCES_DIR}/${APP_NAME}.icns" \
	--window-size 500 300 \
	--icon-size 96 \
	--icon ${APP_NAME}.app 135 102 \
	--hide-extension ${APP_NAME}.app \
	--app-drop-link 365 102 \
	${DMG_NAME} \
	${APP_NAME}.app
