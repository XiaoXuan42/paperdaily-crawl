# Paper Daily

**Paper Daily** is a simple tool to get what interest you from arxiv based on categories, key words in title/abstract and authors. You can write your configuration in `config.json` and run the flask application to get the result.

## A simple example
`config.json`:
```json
{
    "categories": ["cs.AI"],
    "keywd_in_title": ["Diffusion", "Transformer", "CNN"]
}
```

This configuration means you are interested in papers of `cs.AI` with key word "Diffusion", "Transformer" or "CNN" in the title. Other available options include `keywd_in_abstract`, `authors`. Key word check is case insensitive.

Under the directory of this project, run`python -m flask --app app.flask.app run` to start a flask server. Available url formats are as follows:

1. `/cs/?date=2023-09-21&categories=cs.AI&keywd_in_title=Diffusion,Transformer,CNN`: list papers published/updated in 2023-09-21 of `cs.AI` with "Diffusion", "Transformer" or "CNN" in the title.

Pattern: `/<primary_set>/?date=%Y-%m-%d&categories=<c1>,...,<cn>&keywd_in_title=<kt1>,...,<ktm>&keywd_in_abstract=<ka1>,...,<kap>&authors=<a1>,...,<ar>`

2. `/cs/yesterday`: list papers published/updated in cs primary category yesterday that satisfy the constraints specified by `config.json`.

Available primary set: `cs, econ, physics, q-bio, q-fin, stat, math, eess`

## Roadmap
- [ ] More fancy/useful website
    - [ ] search inputbox
    - [ ] keyword highlight
    - [ ] link to arxiv
- [ ] More intelligent
    - [ ] sort papers according to the configuration
    - [ ] filter by semantic rather than simple phrase-matching
