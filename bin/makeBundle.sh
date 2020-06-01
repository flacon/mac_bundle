#!/bin/bash

# Ver 0.4

set -e

QT_DIR="/usr/local/opt/qt/"

#==============================

if [ "${APP_NAME}" = "" ]; then
	echo "Missing APP_NAME argument in the spec file" >&2
	exit 1
fi


if [ "${SOURCE}" = "" ]; then
	echo "Missing SOURCE argument in the spec file" >&2
	exit 1
fi

if [ "${CERT_IDENTITY}" = "" ]; then
	echo "Missing CERT_IDENTITY argument in the spec file" >&2
	exit 1
fi

if [[ ! -e $SOURCE ]]; then
	echo "$SOURCE not found" >&2
	exit 1
fi

#==============================
BUNDLE_CONTENTS_DIR="${APP_NAME}.app/Contents/"
BUNDLE_BIN_DIR="${APP_NAME}.app/Contents/MacOS"
BUNDLE_LIB_DIR="${APP_NAME}.app/Contents/Frameworks"
BUNDLE_RESOURCES_DIR="${APP_NAME}.app/Contents/Resources"
BUNDLE_TRANSLATIONS_DIR="${BUNDLE_CONTENTS_DIR}/translations"
PATH=${PATH}:${QT_DIR}/bin
#=========================================

function error() {
	echo "Error: $1"
	exit ${2:-10}
}

function checkMinMacOSVer() {
	mac=$(printf  "%05d%05d%05d" $(sw_vers -productVersion | tr '.' ' '))
	need=$(printf "%05d%05d%05d" $(echo $1 | tr '.' ' '))
	[[ $mac -ge $need ]] || return 1
}

function createAppDirs {
	rm -rf ${APP_NAME}.app
	install -d ${APP_NAME}.app
	install -d ${BUNDLE_BIN_DIR}
	install -d ${BUNDLE_LIB_DIR}
	install -d ${BUNDLE_RESOURCES_DIR}
	install -d ${BUNDLE_TRANSLATIONS_DIR}
}


function build() {
	DIR=$1

	if [[ -f $SOURCE ]]; then
		SRC_DIR=${DIR}
		echo "Extract $SOURCE"
		tar xf "${SOURCE}" --directory=${DIR} --strip 1 || exit 2
	elif [[ -d $SOURCE ]]; then
		SRC_DIR="${SOURCE}"
	fi


	BUILD_DIR=${DIR}/build
	install -d  ${BUILD_DIR}

	 
	CUR_DIR=`pwd`

	(
	    cd ${BUILD_DIR} 
	    cmake 	-DMAC_BUNDLE=Yes \
	    		-DCMAKE_INSTALL_PREFIX=${CUR_DIR} \
	    		-DCMAKE_OSX_DEPLOYMENT_TARGET="10.10.1" \
	    		${SRC_DIR}

	    make -j8 && make install && echo "make is OK"
	)
}


function addPrograms() {
	# Executable files ...................................
	for prog in ${THIRD_PARTY_PROGS}; do
		install -m 755 /usr/local/bin/${prog} ${BUNDLE_BIN_DIR}
	done
}


function fixDylibs() {
	echo "** Fix dylibs"

	install_name_tool \
			-change                     @rpath/Sparkle.framework/Versions/A/Sparkle \
		        @executable_path/../Frameworks/Sparkle.framework/Versions/A/Sparkle \
				Flacon.app/Contents/MacOS/Flacon

	cp -PR ~/Library/Frameworks/Sparkle.framework "${BUNDLE_LIB_DIR}"


	for prog in ${THIRD_PARTY_PROGS}; do
		dylibbundler 	--overwrite-files \
						--bundle-deps \
						--fix-file ${BUNDLE_BIN_DIR}/${prog} \
						--dest-dir "${BUNDLE_LIB_DIR}" \
						--install-path @executable_path/../Frameworks/ > /dev/null
	done

	macdeployqt  ${APP_NAME}.app -always-overwrite


	# Checks
	err=""
	for f in flacon ${THIRD_PARTY_PROGS}; do
		libs=$(otool -L ${BUNDLE_BIN_DIR}/$f | grep -v "${BUNDLE_BIN_DIR}\|@executable_path\|/usr/lib/\|/System/Library/Frameworks/" || echo "")

		if [ -n "${libs}" ]; then
			echo "$f Not all libraries are local ${libs}"
			err="1"
		fi
	done

	[ "$err" = "" ] || exit 10
}


function sign() {
	################################################
	# Sign

	echo "** Sign files"
	codesign --force --deep --verify  --sign "${CERT_IDENTITY}" ${APP_NAME}.app || error "codesign is failed"

	echo "** Checks"
	if checkMinMacOSVer "10.11.0"; then
		codesign -v --strict --deep --verbose=1 ${APP_NAME}.app || error "codesign check is failed"
	else
		# Old versions of codesign don't support --strict option
		codesign -v --deep --verbose=1 ${APP_NAME}.app
	fi
	
	spctl --assess --type execute ${APP_NAME}.app || error "spctl check is failed"
}


function makeDmg() {
	if [[ $MAKE_DMG = "Yes" ]]; then
		echo "** Make DMG image"
		VERSION=`/usr/libexec/PlistBuddy -c "print :CFBundleVersion" ${APP_NAME}.app/Contents/Info.plist`
		DMG_NAME=${DMG_PATTERN:=\{APP_NAME\}}
		DMG_NAME=${DMG_NAME/\{APP_NAME\}/${APP_NAME}}
		DMG_NAME=${DMG_NAME/\{VERSION\}/${VERSION}}
		dmgbuild -s dmg_settings.py "$APP_NAME" "${DMG_NAME}"
	fi
}

PATH=${PATH}:$(dirname "$BASH_SOURCE")


TMP_BUILD_DIR=$(mktemp -d /tmp/boomaga_pkg.XXXXXX)

createAppDirs
build "${TMP_BUILD_DIR}"
addPrograms
fixDylibs
sign
makeDmg

rm -rf ${TMP_BUILD_DIR}
