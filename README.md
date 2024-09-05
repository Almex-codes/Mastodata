Mastodata is a tool set to collect timeline data from Mastodon instances and to display and analyze the collected data. Data collection is based on the Mastodon API and the python wrapper for it (Mastodon.py).

1) Data collection:
Mastodata_hashtag.py and Mastodata_Local_Public.py are used to collect data and save it in json files. While the time frame of the collected data is flexible for Mastodata_hashtag.py, Mastodata_Local_Public.py needs to be automated. In test runs requests were conducted on an hourly basis, automated by cron.

2) Data display and analysis:
The analysis notebook files visualize data in different ways. analysis_notebook_hashtag.ipynb and analysis_notebook_local+public.ipynb visualize the data of their counterparts from data collection, only a path of the folder containing the json files needs to be provided.
analysis_notebook_fedidb.ipynb however does not display saved files. It requests all self-registered servers/instances listed on 'fedidb.org'. This includes also non-Mastodon sites, e.g. using Pleroma, Lemmy, etc. It was mainly used to extract Mastodon domains but can also be modified to filter for domains of any social media type on the Fediverse.

Files:

analysis_notebook_fedidb.ipynb

analysis_notebook_hashtag.ipynb

analysis_notebook_local+public.ipynb

Mastodata_hashtag.py

Mastodata_Local_Public.py

Installation:
After installing the requirements from the requirenments.txt file Mastodata files work "right out of the box". Mastodata was only tested on Python 3.10.14 and above.


Usage:

Detailled description can be found within the first section of each file.


Logs:

Logs are only created for Mastodata_Local_Public.py (mastodata_local_pubic.log) and Mastodata_hashtag.py (mastodata_hashtag.log).
For Mastodata_Local_Public.py the log contains the amount of collected posts for each instance and timeline (local and public) specified as well as the time of the code's execution.
Mastodata_hashtag.py contains the same information. However the more instances posts get collected from, the larger the log gets. Keep that in mind when doing Mastodon wide requests.
Error messages contain the name of the instance, where the request failed. This usually happens, when an instance has their public API access disabled.






