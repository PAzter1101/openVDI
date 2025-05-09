#!/bin/sh

if ! (docker ps >/dev/null 2>&1) ; then
	echo "docker daemon not running, will exit here!" ;
	exit 1 ;
fi

echo "Preparing folders and creating ./init/initdb.sql" ;
mkdir ./init >/dev/null 2>&1 ;
chmod -R +x ./init ;
mkdir ./record >/dev/null 2>&1 ;
chmod -R 777 ./record ;
docker run --rm guacamole/guacamole /opt/guacamole/bin/initdb.sh --postgresql > ./init/initdb.sql ;
echo "done" ;

