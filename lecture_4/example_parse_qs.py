from sys import argv


from urllib.parse import unquote


def parse_qs(query_string: str) -> dict:
    result = {}
    pairs = query_string.split("&")

    for pair in pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            key = unquote(key)
            value = unquote(value)
        else:
            key, value = unquote(pair), ""

        if key in result:
            if isinstance(result[key], list):
                result[key].append(value)
            else:
                result[key] = [result[key], value]
        else:
            result[key] = value

    return result


if __name__ == "__main__":
    query_string = argv[1]
    print(parse_qs(query_string))
