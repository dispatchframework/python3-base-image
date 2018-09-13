def dummy(context, payload):
    print("hello dummy")
    payload["function"] = "dummy"
    return payload
