#!/bin/bash
GEONATURE_DIR=$1
MODULE_DIR=$(readlink -e "${0%/*}")/

ln -nsf $MODULE_DIR/config/monitorings $GEONATURE_DIR/config/modules/.
