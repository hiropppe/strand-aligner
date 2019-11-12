A little modified [STRANDAligner](https://github.com/jrs026/STRANDAligner) including python3 support

# STRAND Aligner
An implementation of the HTML alignment algorithm of STRAND:

P. Resnik and N. A Smith. The web as a parallel corpus. Computational
Linguistics, 29(3):349-380, 2003.

This also contains an implementation of the Gale and Church sentence alignment
algorithm:

W. A. Gale and K. W. Church. A program for aligning sentences in
bilingual corpora. Computational Linguistics, 19:75-102, March 1993.

## Installation
```
$ make
$ make install
```

## Usage
```
$ cd test
$ python gen_sample.py -l1 en -l2 ja -u1 http://ahatoro.com/en/aha-toro -u2 http://ahatoro.com/ja/aha-toro | gzip -c > ahatoro.gz
$ strand-align -i ahatoro.gz -o test
# *.ann format (alignment metadata for each document pair)
# <left url>\t<right url>\t<offset>\t<number of alignments>\t<difference percentage>\t<left sequence length>\t<right sequence length>
$ cat test.ja-en.ann 
http://ahatoro.com/ja/aha-toro	http://ahatoro.com/en/aha-toro	0	33	0.000000	207	207
# alignment format
# <left sequence>\t<left text>\t<right sequence>\t<right text>\t<alignment cost>
$ cat test.ja-en
3	Aha Toro | Aha Toro	3	Aha Toro | Aha Toro	0.000000
8	Jump to Navigation	8	Jump to Navigation	0.000000
19	menu	19	menu	0.000000
28	HOME	28	HOME	0.000000
30	AHA TOROの家	30	The house of AHA TORO	0.000000
36	AHA TORO	36	AHA TORO	0.000000
38	上昇したレジェンド	38	The legend that gave rise	0.000000
44	PRODUCTS	44	PRODUCTS	0.000000
46	多種多様な味比類のない	46	Wide variety, flavor unmatched	0.000000
52	PRESENCE	52	PRESENCE	0.000000
54	15カ国以上で認められ	54	Recognized in over 15 countries	0.000000
60	ELABORATION	60	ELABORATION	0.000000
62	詳細かつ正確なプロセス	62	A detailed and accurate process	0.000000
68	CONTAC US	68	CONTAC US	0.000000
70	いつもあなたからの聴取の興味	70	Always interested in hearing from you	0.000000
84	Basa-basa	84	Languages	0.000000
89	Español	89	Español	0.000000
92	English	92	English	0.000000
95	日本語	95	日本語	0.000000
98	繁體中文	98	繁體中文	0.000000
113	aha-toro	113	aha-toro	0.000000
130	Aha Toro	130	Aha Toro	0.000000
144	AHA TORO	144	AHA TORO	0.000000
150	TORO（トロ）とは、勇猛で辛抱強く、また優れた決断力のある雄牛のこと。彼らは果てしなく広がる青く瑞々しいアガベ畑をまるで領主のように歩いていく。彼らの粋と伝統が、その不老不死の妙薬に己の命を捧げる覚悟をさせていた。	150	“Toro” was a brave and persevering bull; possessing a great determination. He would walk, as the absolute owner of those unending blue-colored fields of, ripe and proud agave plants. Fruit of their loins, and with much tradition; they were ready to sacrifice themselves to give life to that precious elixir.	0.000000
153	TOROの眠る事なき魂とその黒光る毛皮が、孤独な夜の静寂を分かち合う青い大地と混ざり合う。そして夜の終わりには、刈り取られたばかりのアガベが横たわる小屋へと走り去って行く。	153	“Toro’s” restless soul, and beautiful black fur blended with the blue fields; allies in taking advantage of the solitary quietness of the night….and at days end, run off to the warehouse where the freshly cut fruits of the agave plant lay.	0.000000
156	彼は初めて忍び込む事に成功する。TOROはテキーラの魂とでも言おうご馳走をむさぼる。まるで神がその犠牲を、その土地に引き続き繁栄をもたらすことを認めたかのように。	156	His first raids were successful. “Toro” enjoyed insatiable feasts; devouring the very soul of the tequila, like a god accepting as sacrifice, the bounty of the land to grant its continued prosperity.	0.000000
159	直後、労働者達はTOROにとっての快楽、彼らにとっての冒涜を止めさせるために番を張る。夜ごと、大きな声が響き渡る。「Aha, TORO! 雄牛ども！向こうへ行け！アーハ！トロ！」	159	Soon after, the workers stood guard to stop what was to them a sacrilege; for “Toro”, an ecstasy. Every night was heard the desperate yells, “Aha Toro! Go away! Aha, aha!”	0.000000
162	その後、柵が作られ、TORO達は小屋へ忍び込む事が出来なくなった。けれど、赤土の大地からの恵みである青い宝石への愛は尽きる事がない。毎夜、彼らは柵を抜け出し、神が作られたイバラの蜜、私達のテキーラの魂を守っている。 そうして、私達のAHA TOROは生まれたのです	162	Then, a wall brought “Toro’s” ventures into the warehouse to an end. However, his love for the blue richness that blended with the red earth did not cease. Since then, each night he leaves his pen to guard and protect the thorned creation of God from where the soul of our tequila, AHA TORO, is born.	0.000000
166	Taste of our land	166	Taste of our land	0.000000
177	Español	177	Español	0.000000
180	English	180	日本語	0.000000
183	繁體中文	183	繁體中文	0.000000
197	Footer	197	Footer	0.000000
```
