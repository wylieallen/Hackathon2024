from Scweet.scweet import scrape
from Scweet.const import load_env_variable
from openai import OpenAI
import json
import dotenv

env_path = '.env'
dotenv.load_dotenv(env_path, verbose=True)
api_key = load_env_variable("OPENAI_KEY", none_allowed=True)
client = OpenAI(api_key=api_key)

sinceDate = "2024-09-01"
untilDate = "2024-09-12"
interval = 11

# Sacramento
# geocode = "38.57745307395626,-121.47710335024563,20km"

data = scrape(words=['"shoot"'],since=sinceDate, until=untilDate, interval=interval,
              headless=False, display_type="Latest", save_images=False, lang="en",
              resume=False, filter_replies=False, proximity=False, limit=30)

system_prompt = 'California Penal Code 422, the statute making it a crime to communicate a threat, reads as follows:\n'
system_prompt = system_prompt + '“Anyone who willfully makes a threat to commit a crime that can result in great bodily injury or death to someone, with the intent that their statement is to be taken as a threat, even if there is no intent to actually carrying it out, which was specific to the person threatened, an immediate prospect of execution of the threat, causing a victim to be in fear of their safety or immediate family.”\n'
system_prompt = system_prompt + 'You are a member of the content moderation team for a social media platform. Your team has been tasked with monitoring the platform for criminal threats of violence. Your job is to evaluate individual posts and assess if the post contains content that could reasonably be considered a credible threat of violence.\n'
system_prompt = system_prompt + 'If you assess the content as containing a threat of violence in violation of California Penal Code 422, you should write a brief summary of the part of the post that constitutes a potential threat and justify your reasoning based on the definition of an online threat of violence, as provided above. Your responses should also contain a description of the possible target of the threat and a verdict of "ACTIONABLE" if there is a clear threat, "OK" if there is clearly no threat, and "NEEDS_CONTEXT" if a clear verdict cannot be rendered from the content of the singular post alone.\n'
system_prompt = system_prompt + 'For integration with automated systems, your response should be in the form of a JSON payload with the following structure: {"justification":[insert-summary-here],"possible_target":[insert-possible-target-here],"verdict":[insert-verdict-here]} (in plain text, without any ```json...``` annotations) \n'

evaluatedMessages = set()

def evaluateMessage(message):
    if message in evaluatedMessages:
        return None
    else:
        evaluatedMessages.add(message)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": 'Evaluate the following message: "' + message + '"'}
        ]
    )
    try:
        obj = json.loads(response.choices[0].message.content)
        return obj
    except json.decoder.JSONDecodeError:
        print('failed to parse chatgpt response payload')
        print('message:')
        print(message)
        print('response:')
        print(response)
        return None

for tweet in data:
    response = evaluateMessage(tweet[3])
    if response is not None and response['verdict'] != 'OK':
        print('input: ')
        print(tweet)
        print('output: ')
        print(response)
        print('================================')

        ####
        # If tweet was actionable, search user's timeline for more actionable/questionable tweets
        # if (response['verdict'] == 'ACTIONABLE'):
        #     actionableTweets = [tweet]
        #     questionableTweets = []
        #     username = tweet[1]
        #     print('searching for more tweets from user ' + username)
        #     tweetsByActionableUser = scrape(from_account=username, since=sinceDate, until=untilDate, interval=interval,
        #                                     headless=False, display_type="Latest", save_images=False, lang="en",
        #                                     resume=False, filter_replies=False, proximity=False, limit=40)
        #     print('scraped ' + str(len(tweetsByActionableUser)) + ' tweets by user ' + username)
        #     for tweet2 in tweetsByActionableUser:
        #         response2 = evaluateMessage(tweet2[3])
        #         if response2 is not None and response2['verdict'] != 'OK':
        #             print('input: ')
        #             print(tweet2)
        #             print('output: ')
        #             print(response2)
        #             print('================================')
        #             if response2['verdict'] == 'ACTIONABLE':
        #                 actionableTweets.append(tweet2)
        #             elif response2['verdict'] == 'NEEDS_CONTEXT':
        #                 questionableTweets.append(tweet2)
        #     print('found ' + str(len(actionableTweets)) + ' actionable tweets and ' + str(len(questionableTweets)) + ' questionable tweets by user ' + username)

print('done')