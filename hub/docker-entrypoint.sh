#!/bin/sh
set -e
inst="${INSTANCE_NAME:-example}"
sed "s/__INSTANCE_NAME__/${inst}/g" /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
