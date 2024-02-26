## doogle

A discord bot that searches google images.

You will need to set up a [google programmable search engine](https://developers.google.com/custom-search/docs/tutorial/creatingcse). You will also need a `keys.json` file in the same directory as the bot. The format looks like this:

```
{
    "discord": "discord bot api key",
    "google": "google api key",
    "pse_engine_id": "google programmable search engine id"
}
```