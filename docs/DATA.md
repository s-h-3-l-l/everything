### CONFIG FILE
```
{
    "subs" : [
        {
            "module" : (string),
            "category" : (string),
            "url" : (string)
        }
    ],
    "cats" : [
        (string)
    ],
    "timer" : (null|integer)
}
```

### FEED FILE
```
[
    {
        "module" : (string),
        "source" : (string),
        "headline" : (string),
        "thumbnail" : (string|null),
        "content" : (string),
        "category" : (string|null),
        "sub" : (string) # URL,
        "timestamp" : (integer),
        "link" : (string|null)
    }
]
```
