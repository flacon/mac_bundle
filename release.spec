#!/bin/bash

APP_NAME="Flacon"

SOURCE=flacon-7.0.1.tar.gz

THIRD_PARTY_PROGS="faac flac lame mac metaflac mp3gain oggenc opusenc sox ttaenc vorbisgain wavpack wvgain wvunpack"

CERT_IDENTITY="Developer ID Application: Alex Sokolov (635H9TYSZJ)"

DMG_PATTERN={APP_NAME}_{VERSION}
MAKE_DMG=Yes

. ./bin/makeBundle.sh