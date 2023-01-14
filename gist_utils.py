import requests
import pyUnicodeSteganography as us


gistApiUrl = "https://api.github.com/gists"
gistHeaders = None
gistPostData = {
    "description": "William Shakespeare enthusiasts",
    "public": False,
    "files": {
        "README.md": {
            "content":"William Shakespeare enthusiasts - discussion thread"
        }
    }
}


def initializeGistHeaders(token):
    global gistHeaders
    gistHeaders = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }


# creates a new gist and returns its URL
def createGist() -> str:
    return requests.post(
        url = gistApiUrl, 
        json = gistPostData,
        headers = gistHeaders
    ).json()["url"]


COMMENTS_FETCH_LIMIT = 30
# fetches and returns the last comment or None if there are no comments
def fetchLastComment(gistUrl : str) -> dict | None:
    allComments = []
    page = 1
    while True:
        params = {
            "per_page": COMMENTS_FETCH_LIMIT,
            "page": page,
        }
        fetchedComments = requests.get(
            url = gistUrl + "/comments",
            headers = gistHeaders,
            params = params
        ).json()

        allComments.extend(fetchedComments)
        if len(fetchedComments) < COMMENTS_FETCH_LIMIT:
            break
        else:
            page += 1

    return allComments[-1] if allComments else None


# creates a new comment with the given body as its text
def addComment(gistUrl : str, body : str) -> None:
    data = {
        "body": f"{body}"
    }
    requests.post(
        url = gistUrl + "/comments", 
        json = data,
        headers = gistHeaders
    )


# uses text (unicode) steganography to encode the given secret text message into the given cover text message
def encodeMessage(coverText : str, secret : str) -> str:
    return us.encode(coverText, secret)


# uses text (unicode) steganography to decode the secret text message from the encoded text message
def decodeMessage(encodedText : str) -> str:
    return us.decode(encodedText)
