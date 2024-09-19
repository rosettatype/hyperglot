September 2024, contributors added on a per-language basis. To reconstruct how
contributions were identified consult the below.

Particularly, there are a few points in the repo history when:
- The current data/xxx.yaml were in separate folders per language
- The data was in a single file in lib/hyperglot/hyperglot.yaml
- The data originally was in a single file in data/rosetta.yaml


In addition/conjunction with CONTRIBUTORS.txt:

Get a list of all authors with merged commits:

git shortlog -sec

      2  Caleb Maclennan <caleb@alerque.com>
    172  David Březina <david@rosettatype.com>
    10  David Březina <david@rosettatype.com>
     2  David Corbett <corbett.dav@northeastern.edu>
   113  Denis Moyogo Jacquerye <moyogo@gmail.com>
     3  Fredrick Brennan <copypaste@kittens.ph>
    70  GitHub <noreply@github.com>
     3  Gustavo Costa <gusbemacbe@gmail.com>
     5  James A. Crippen (Dzéiwsh) <jcrippen@gmail.com>
   399  Johannes Neumeier <hello@johannesneumeier.com>
     3  Justin Penner <46039243+justinpenner@users.noreply.github.com>
     1  Mathieu Reguer <mathieu.reguer@gmail.com>
     1  Roberto Arista <arista.rob@gmail.com>
     5  Sergio Martins <d.sergiomartins@gmail.com>
    16  Sergio Martins <sergio@typesettings.net>
     2  lipsumtype <sanikidzeana9@gmail.com>

L = legacy, hyperglot.yaml


Get a list of all files touched by an author:

user=...
git whatchanged --author="${user}" --no-commit-id --name-only >> ${user}.txt

or

git log --committer="${user}"


Note that pre ~0.5.0 all languages were in one joint hyperglot.yaml, so for those
users checkout d7d405d5a092d9e7da13254e7b61230c59eaa271 and from there get their changes,
e.g. with:

git blame lib/hyperglot/hyperglot.yaml --ignore-revs-file ignore-revs.txt

f30243fa63549338eb0e2851ec8b6f1af826884e
91d577548482823f955326a995fab0d3496db273

And before dec009f69e3132074ac7ab40eb0b9ee37f0235fd:

git blame data/rosetta.yaml --ignore-revs-file ignore-revs.txt
