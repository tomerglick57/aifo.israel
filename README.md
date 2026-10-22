# aifo.israel
The official repo for איפה.ישראל


[![Star History](https://api.star-history.com/svg?repos=tomerglick57/aifo.israel&type=Date)](https://star-history.com/#tomerglick57/aifo.israel&Date)

## API

For when you need to know where Israel is, programmatically:

```bash
curl https://xn--4dbio8b.xn--4dbrk0ce/api/v1/where.json
```

```json
{
  "question": "איפה ישראל?",
  "answer": "הנה פה!",
  "country": "Israel",
  "country_code": "IL",
  "latitude": 31.5,
  "longitude": 34.75,
  "map": "https://xn--4dbio8b.xn--4dbrk0ce/israel_on_the_map.svg"
}
```

It's a static file deployed with the site (the hostname is איפה.ישראל in punycode, which every HTTP client understands). The coordinates are the CIA World Factbook's for Israel.