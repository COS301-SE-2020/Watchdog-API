// exports.handler = async (event) => {
//     // TODO implement
//     const response = {
//         statusCode: 200,
//         headers: {"Access-Control-Allow-Origin": "*", 
//         "Access-Control-Allow-Methods": "GET,PUT,POST,DELETE,PATCH,OPTIONS"}
        
//         body: JSON.stringify('Successful'),
//     };
//     return response;
// };

exports.handler = async (event) => {
    const response = {
        statusCode: 200,
        headers: {
            "Access-Control-Allow-Headers" : "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET,DELETE"
        },
        body: JSON.stringify('Hello from Lambda!'),
    };
    return response;
};