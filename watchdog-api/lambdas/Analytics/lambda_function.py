from owner_analytics import *
from dashboard_analytics import *


def error(msg):
    return {
        "status": "ERROR",
        "message": f'Encountered an Unexpected Error: {msg}'
    }


# Bundle the response with an OK
def success(msg, extra={}):
    return {
        "status": "OK",
        "message": f'Operation Completed with Message: {msg}',
        "data": extra
    }


def lambda_handler(event, context):
    route = event['resource']
    params = event['queryStringParameters']
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

    end_date = params['end_date']
    print(f"TEMP end date: {end_date}")

    if "profile" in route:
        time_scale = params['time_scale']
        try:
            # profile analytics
            # 1. preprocess data - load profiles with data structure of graph
            profiles, whitelist = get_profile_data(user_id)
            print(f"(1.1 get profile data): profiles:{profiles}    whitelist:{whitelist}")
            # 2. load data - go through whitelist images and add the images to specified list
            graph_skeleton, intervals = get_profile_template_data(end_date, time_scale)
            print(f"(2): intervals: " + str(intervals))
            graph_data = []
            for profile in profiles:
                graph_data.append(
                    {
                        "id": profile["name"],
                        "aid": profile["aid"],
                        "color": f"hsl({randint(0, 10) * 36},100%,50%)",
                        "data": deepcopy(graph_skeleton)
                    }
                )

            graph_data = populate_graph_data(graph_data, whitelist, intervals, user_id)
            print(f"(3. graph populated data): graph data:{graph_data}")
            resp = success(f"Successfully retrieved graph data for interval {time_scale}", graph_data)
        except Exception as e:
            print(e)
            resp = error(f'Could not complete Profile Analytics due to Error: {e}')
    elif "dashboard" in route:
        try:
            whitelist, blacklist = get_detected_data(user_id)
            print(f"(1. get detected image data): whitelist:{whitelist} blacklist:{blacklist}")
            detected_images = [whitelist, blacklist]
            labels, datasets, intervals = get_dashboard_template_data(end_date)
            print(f"(2. dashboard template data): labels:{labels}   datasets:{datasets}    intervals:{intervals}")
            for i, dataset in enumerate(datasets):
                dataset['data'] = get_y_points_from_set(detected_images[i], intervals)
            data = {
                "labels": labels,
                "datasets": datasets
            }
            print("(3. data to return): data:" + str(data))
            resp = success(f"Successfully retrieved graph data", data)
        except Exception as e:
            print(e)
            resp = error(f'Could not complete Dashboard Analytics due to Error: {e}')

    return {"statusCode": 200, "headers": {"Access-Control-Allow-Origin": "*"}, "body": json.dumps(resp)}
