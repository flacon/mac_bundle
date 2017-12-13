#!/bin/bash

APP_NAME="Flacon"
VERSION=3.1.1

SRC_DIR=~/myPrograms/flacon/macos
ICONSET_DIR=${SRC_DIR}/images/mainicon/flacon.iconset
QT_DIR="/usr/local/opt/qt/"

BUNDLE_CONTENTS_DIR="${APP_NAME}.app/Contents/"
BUNDLE_BIN_DIR="${APP_NAME}.app/Contents/MacOs"
BUNDLE_LIB_DIR="${APP_NAME}.app/Contents/Frameworks"
BUNDLE_RESOURCES_DIR="${APP_NAME}.app/Contents/Resources"
BUNDLE_TRANSLATIONS_DIR="${BUNDLE_CONTENTS_DIR}/translations"

THIRD_PARTY_PROGS="faac flac lame mac metaflac mp3gain oggenc opusenc ttaenc vorbisgain wavpack wvgain wvunpack"
#=========================================
BUILD_DIR=~/myPrograms/flacon/macos/build

PATH=${PATH}:${QT_DIR}/bin


set -e 

rm -rf ${APP_NAME}.app

(
    install -d ${BUILD_DIR}
    cd ${BUILD_DIR} 
    cmake -DMAC_BUNDLE=Yes ${SRC_DIR} 
    make -j8 && echo "make is OK"
)


install -d ${APP_NAME}.app
install -d ${BUNDLE_BIN_DIR}
install -d ${BUNDLE_LIB_DIR}
install -d ${BUNDLE_RESOURCES_DIR}
install -d ${BUNDLE_TRANSLATIONS_DIR}



# Executable files ...................................
install -m 755 ${BUILD_DIR}/flacon ${BUNDLE_BIN_DIR} 
for prog in ${THIRD_PARTY_PROGS}; do
	install -m 755 /usr/local/bin/${prog} ${BUNDLE_BIN_DIR}
done

# Translations .......................................
install -m 644 ${BUILD_DIR}/flacon_*.qm                  ${BUNDLE_TRANSLATIONS_DIR}/
install -m 644 ${QT_DIR}/translations/*.qm            ${BUNDLE_TRANSLATIONS_DIR}/


# Resources ..........................................
install -m 644 ${BUILD_DIR}/flacon.1.gz ${BUNDLE_RESOURCES_DIR}


cat ${BUILD_DIR}/Info.plist  | sed -e "s/%VERSION%/${VERSION}/g" | grep "\S" > ${APP_NAME}.app/Contents/Info.plist

# Icons ..............................................
iconutil --convert icns --output ${APP_NAME}.app/Contents/Resources/${APP_NAME}.icns ${ICONSET_DIR}


echo "*******************************************"
echo "** Fix dylibs"

for prog in ${THIRD_PARTY_PROGS}; do
	./dylibbundler 	--overwrite-files \
					--bundle-deps \
					--fix-file ${BUNDLE_BIN_DIR}/${prog} \
					--dest-dir "${BUNDLE_LIB_DIR}" \
					--install-path @executable_path/../Frameworks/ > /dev/null
done 

macdeployqt  ${APP_NAME}.app -always-overwrite
#macdeployqt  ${APP_NAME}.app -always-overwrite -dmg


echo "*******************************************"
echo "** Checks "
for f in flacon ${THIRD_PARTY_PROGS}; do
	
	libs=$(otool -L ${BUNDLE_BIN_DIR}/$f | grep -v "${BUNDLE_BIN_DIR}\|@executable_path\|/usr/lib/")

	if [ -n "${libs}" ]; then
		printf "\n  $f Not all libraries are local\n%s\n" "${libs}"
	fi
done

exit 0