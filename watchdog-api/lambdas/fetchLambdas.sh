download_code () {
    local OUTPUT=$1
    aws lambda get-function --function-name $OUTPUT --query 'Code.Location' | xargs wget -O ./lambda_functions/$OUTPUT.zip  
}

mkdir -p lambda_functions

for run in $(aws lambda list-functions --output text --query 'Functions[].FunctionName');
do
	echo $run
    aws lambda get-function --function-name $run --query 'Code.Location' | xargs wget -O $run.zip
    unzip -d $run/ $run.zip
done

echo "Completed Downloading all the Lamdba Functions!"