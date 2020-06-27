# Zip Files
for f in ./*/*.py ; do
	echo "\tZIPPING FILES..."
	echo "$f" | sed  -E "s/^.*\/(.*)\/(.*)/\1.zip \1\/\2/" | xargs zip -r
	echo "\tCOMPILING PATHS..."
	nf=$(echo "$f" | sed -E "s/^.*\/(.*)\/(.*)/\1/")
	pth=$(find $PWD -type f | grep $nf.zip)
	echo "\tDEPLOYING $nf TO AWS using $nf.zip in $pth..."
	aws lambda update-function-code \
		--function-name $nf \
		--zip-file fileb://$pth
	echo "DONE."
done
