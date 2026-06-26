# Eval Report: Qwen3-4B · Template id=4 · constrained_beam_search

## 實驗設定

| 項目 | 值 |
|---|---|
| 模型 | Qwen3-4B |
| LoRA | `checkpoints/Qwen3-4B/run_3/lora_final` |
| Template ID | 4 |
| 評估筆數 | 5,000 |
| Max guess | 1,000 |
| 搜尋法（primary） | `constrained_beam_search` |
| 搜尋法（fallback） | `dynamic_beam_search`（當 tags 含 pos/pos_semantic 時） |
| 測試集 | `datasets/processed/semanticPCFG/000webhost/backoff/split/test_data.jsonl` |
| 輸出檔 | `results/eval-245621.out` |

## Crack Rate

| @K | Cracked | Rate |
|---|---|---|
| @1 | 74 / 5,000 | 1.48% |
| @10 | 130 / 5,000 | 2.60% |
| @100 | 243 / 5,000 | 4.86% |
| @1000 | 367 / 5,000 | 7.34% |

## 結果圖表

![Crack Rate & Tag Distribution](../../gen/results/Qwen3-4B_id4_constrained_beam_search_result.png)

## 破解密碼的 Tag 類型分佈

Log parsing 共解析到 359 筆（官方統計 367 筆；8 筆因 log 格式邊界案例未收錄）。

| Tag 類型 | 筆數 | 比例 |
|---|---|---|
| 純 backoff tag | 12 | 3.3% |
| 含 pos / pos_semantic tag | 347 | 96.7% |

> **觀察：** 絕大多數被破解的密碼都含有 pos/pos_semantic tag，透過 fallback 到 dynamic_beam_search 才被破解。純 backoff tag 密碼極少被破解，代表 constrained_beam_search 在 backoff 結構上的實際破解能力很有限。

## 破解密碼列表

格式：`idx | pw | rank | has_pos_semantic | tags`

```
   25 | greenday007                    |    5 | True  | green.s.01|day.n.01|number3
   26 | iseerainbows1                  |   89 | True  | ppis1|see.v.01|rainbow.n.01|number1
   37 | livetodie1                     |  249 | True  | populate.v.01|to|die.v.01|number1
   40 | 12apower                       |    1 | True  | number2|at1|power.n.01
   45 | welcome12                      |    1 | True  | welcome.v.01|number2
   65 | completeman09                  |    9 | True  | complete.a.01|man.n.01|number2
   95 | godlike1                       |  213 | True  | divine.s.05|number1
  116 | speedy78                       |  561 | True  | rapid.s.02|number2
  121 | wordup12                       |    1 | True  | word.n.01|up.r.01|number2
  124 | friday13                       |    9 | True  | friday.n.01|number2
  134 | 24info24                       |  173 | True  | number2|information.n.01|number2
  155 | 123456789+                     |    1 | False | number9|special1
  232 | burgerking2                    |    9 | True  | burger.n.01|king.n.01|number1
  274 | mailing1                       |   19 | True  | mailing.n.01|number1
  275 | peace12345                     |    3 | True  | peace.n.01|number5
  276 | night457                       |  755 | True  | night.n.01|number3
  284 | forumbest55                    |  177 | True  | forum.n.01|best.r.01|number2
  285 | badboy75                       |  417 | True  | bad.a.01|male_child.n.01|number2
  314 | goodmiracle21                  |   81 | True  | good.a.01|miracle.n.01|number2
  324 | ahimsa13                       |    5 | True  | ahimsa.n.01|number2
  326 | 123456as123456                 |   72 | False | number6|char2|number6
  339 | 01matrix1                      |   37 | True  | number2|matrix.n.01|number1
  345 | 1212money                      |  101 | True  | number4|money.n.01
  346 | darksky123                     |    1 | True  | dark.a.01|sky.n.01|number3
  369 | blind1234                      |    1 | True  | blind.a.01|number4
  378 | unavailable1                   |    1 | True  | unavailable.a.01|number1
  402 | counter42                      |   89 | True  | counter.n.01|number2
  419 | jakejake1                      |   41 | True  | mname|mname|number1
  428 | 12345678ka                     |  324 | False | number8|char2
  431 | mcan2008                       |   29 | True  | char1|can.v.01|number4
  432 | keept4ever                     |  721 | True  | keep.v.01|char1|number1|ever.r.01
  459 | anima420                       |  121 | True  | anima.n.01|number3
  479 | freewild999                    |   29 | True  | free.a.01|wild.a.01|number3
  521 | cupacups1                      |    9 | True  | cup.n.01|at1|cup.v.01|number1
  525 | asura123                       |    1 | True  | asura.n.01|number3
  536 | brave2008                      |    3 | True  | brave.a.01|number4
  539 | online07                       |    9 | True  | on-line.a.01|number2
  583 | misterphd123                   |    1 | True  | mister.n.01|ph.d..n.01|number3
  592 | fury1234                       |    1 | True  | fury.n.01|number4
  606 | jaguar2121                     |  553 | True  | jaguar.n.01|number4
  611 | mylove82                       |  281 | True  | appge|love.n.01|number2
  619 | 2iceberg14                     |  273 | True  | number1|iceberg.n.01|number2
  664 | arctic09                       |    7 | True  | north-polar.s.01|number2
  675 | flamelight007                  |   21 | True  | fire.n.03|light.n.01|number3
  679 | spring2009                     |    3 | True  | spring.n.01|number4
  687 | robert77                       |  285 | True  | mname|number2
  691 | hotsauce3                      |    9 | True  | hot.a.01|sauce.n.01|number1
  703 | 1234567bb                      |  211 | False | number7|char2
  705 | passwords3                     |   27 | True  | password.n.01|number1
  755 | energizer0                     |    3 | True  | energizer.n.01|number1
  797 | butter10                       |    3 | True  | butter.n.01|number2
  799 | scorpions32                    |  289 | True  | scorpio.n.01|number2
  804 | down4you13                     |  289 | True  | down.r.01|number1|ppy|number2
  809 | 0computer                      |    5 | True  | number1|computer.n.01
  825 | gorilla123                     |    1 | True  | gorilla.n.01|number3
  836 | cradle_66                      |  585 | True  | cradle.n.01|special1|number2
  847 | secret23                       |   19 | True  | secret.s.01|number2
  852 | sunset135                      |   35 | True  | sunset.n.01|number3
  858 | finland123                     |  155 | True  | country|number3
  868 | thedoors1                      |   45 | True  | at|door.n.01|number1
  890 | tunerillas3                    |    9 | True  | tuner.n.01|ill.a.01|csa|number1
  939 | skither7                       |  109 | True  | skit.n.01|appge|number1
  945 | heyheynow1                     |   17 | True  | uh|uh|now.r.01|number1
  950 | virus123456                    |    1 | True  | virus.n.01|number6
  953 | bookmark1234                   |    1 | True  | bookmark.n.01|number4
  961 | admin_data                     |    5 | True  | nn1|special1|data.n.01
  982 | dreama2004                     |   37 | True  | dream.n.01|at1|number4
 1014 | 234567asd                      |  285 | False | number6|char3
 1041 | moonflower88                   |   77 | True  | moonflower.n.01|number2
 1047 | passass1                       |  181 | True  | pass.v.01|char3|number1
 1048 | Shadow123456                   |   39 | True  | shadow.n.01|number6
 1054 | getlow123                      |    1 | True  | get.v.01|low.a.01|number3
 1057 | damageking12                   |    1 | True  | damage.n.01|king.n.01|number2
 1063 | atom2009                       |    5 | True  | atom.n.01|number4
 1067 | iamtheman1                     |    1 | True  | ppis1|be.v.01|at|man.n.01|number1
 1094 | mydear1982                     |  233 | True  | appge|beloved.s.01|number4
 1117 | admin1982                      |  339 | True  | nn1|number4
 1137 | bolec100                       |  777 | True  | bole.n.01|char1|number3
 1141 | corndogs11                     |  453 | True  | corn.n.01|dog.n.01|number2
 1154 | saffron1                       |    1 | True  | saffron.n.01|number1
 1168 | rebirth3                       |  503 | True  | metempsychosis.n.01|number1
 1170 | 13miracles                     |    3 | True  | number2|miracle.n.01
 1178 | 123456kwe                      |   29 | True  | number6|char1|ppis2
 1186 | iamgenius786                   |  529 | True  | ppis1|be.v.01|genius.n.01|number3
 1191 | manxpower1                     |    1 | True  | manx.a.01|power.n.01|number1
 1211 | mianali123                     |   57 | True  | char2|anal.a.01|ppis1|number3
 1231 | confident09                    |    5 | True  | confident.a.01|number2
 1237 | angel_56                       |  753 | True  | angel.n.01|special1|number2
 1241 | ccash123                       |   25 | True  | char1|cash.n.01|number3
 1260 | supermarket69                  |   79 | True  | supermarket.n.01|number2
 1270 | recall123                      |    5 | True  | remember.v.01|number3
 1300 | killer10                       |    5 | True  | killer.n.01|number2
 1304 | boones12                       |   21 | True  | boone.n.01|number2
 1305 | power1234                      |    1 | True  | power.n.01|number4
 1310 | freeagent0100                  |  521 | True  | free.a.01|agent.n.01|number4
 1321 | swat1lost2                     |  417 | True  | swat.n.01|number1|lose.v.01|number1
 1348 | freeman88                      |   59 | True  | freeman.n.01|number2
 1363 | cocacola2006                   |   33 | True  | erythroxylon_coca.n.01|cola.n.01|number4
 1374 | chinping77                     |  117 | True  | chin.n.01|ping.n.01|number2
 1406 | camaleon2                      |   73 | True  | vm|male.a.01|ii|number1
 1408 | yellow21                       |   37 | True  | yellow.s.01|number2
 1410 | dustybottoms1                  |  237 | True  | dusty.s.01|bottom.n.01|number1
 1414 | answer123                      |    1 | True  | answer.n.01|number3
 1437 | snooker22                      |   41 | True  | snooker.n.01|number2
 1453 | sport200                       |   41 | True  | sport.n.01|number3
 1457 | karate20                       |   33 | True  | karate.n.01|number2
 1460 | artist38                       |  159 | True  | artist.n.01|number2
 1465 | redhot78                       |  205 | True  | red.s.01|hot.a.01|number2
 1467 | redhotnet23                    |   65 | True  | red.s.01|hot.a.01|net.a.01|number2
 1472 | wik123456789                   |   40 | False | char3|number9
 1481 | sparty1234                     |  141 | True  | char1|party.n.01|number4
 1482 | iamlegend12                    |    1 | True  | ppis1|be.v.01|legend.n.01|number2
 1483 | chilla68                       |  405 | True  | chill.n.01|at1|number2
 1490 | goodnice123                    |    1 | True  | good.a.01|nice.a.01|number3
 1520 | 12andre12                      |  339 | True  | number2|mname|number2
 1521 | blacks77                       |  479 | True  | black.n.01|number2
 1525 | webclass1                      |    1 | True  | web.n.01|class.n.01|number1
 1537 | nether2121                     |  653 | True  | nether.s.01|number4
 1540 | listenland1                    |    1 | True  | listen.v.01|land.n.01|number1
 1554 | strike123456                   |    1 | True  | strike.n.01|number6
 1613 | jefferson123                   |  277 | True  | mname|number3
 1644 | rock1000                       |   47 | True  | rock.n.01|number4
 1649 | blackout10                     |    5 | True  | blackout.n.01|number2
 1668 | Redtree1                       |   81 | True  | red.s.01|tree.n.01|number1
 1672 | blackmaster1                   |    1 | True  | black.a.01|maestro.n.01|number1
 1683 | jose2008                       |  105 | True  | mname|number4
 1696 | panda111                       |   15 | True  | giant_panda.n.01|number3
 1703 | strike88                       |   63 | True  | strike.n.01|number2
 1723 | 2004balsa                      |   31 | True  | number4|balsa.n.01
 1738 | latino23                       |  323 | True  | latin_american.n.01|number2
 1780 | 123cancer                      |    1 | True  | number3|cancer.n.01
 1786 | lemonsink131                   |  301 | True  | lemon.n.01|sink.n.01|number3
 1795 | friday1956                     |  849 | True  | friday.n.01|number4
 1796 | flame1996                      |  357 | True  | fire.n.03|number4
 1815 | slavisa79                      |  793 | True  | slav.a.01|be.v.01|at1|number2
 1820 | asdfgh123456                   |   46 | False | char4|char2|number6
 1824 | huangyu123                     |  301 | True  | surname|char2|number3
 1844 | binary_pass                    |    9 | True  | binary.a.01|special1|pass.v.01
 1882 | password91                     |  105 | True  | password.n.01|number2
 1887 | ancient13                      |    9 | True  | ancient.s.01|number2
 1892 | munita12                       |    9 | True  | char1|unit_of_measurement.n.01|at1|number2
 1899 | prosperity1                    |    1 | True  | prosperity.n.01|number1
 1916 | nutshe11                       |  237 | True  | nut.n.01|pphs1|number2
 1931 | some1one                       |   41 | True  | dd|number1|mc1
 1941 | none123456                     |   17 | True  | pn|number6
 1942 | parth123                       |   81 | True  | part.n.01|char1|number3
 1943 | master2master                  |    9 | True  | maestro.n.01|number1|maestro.n.01
 1960 | anand123456#                   |  865 | True  | at1|cc|number6|special1
 1973 | online321                      |   25 | True  | on-line.a.01|number3
 1992 | school122                      |  405 | True  | school.n.01|number3
 1997 | paradise21                     |  471 | True  | eden.n.01|number2
 2043 | panzer89                       |   67 | True  | panzer.n.01|number2
 2045 | sport4good                     |   13 | True  | sport.n.01|number1|good.a.01
 2046 | oldsink5                       |   21 | True  | old.a.01|sink.n.01|number1
 2069 | 1z2z3z4z5z                     |  132 | True  | at1|char2|number1|char9|number1|char2
 2094 | myweb4free                     |   33 | True  | appge|web.n.01|number1|free.a.01
 2116 | supermom1                      |    1 | True  | supermom.n.01|number1
 2124 | bigbrother1                    |    1 | True  | large.a.01|brother.n.01|number1
 2139 | blackdance89                   |  109 | True  | black.a.01|dance.n.01|number2
 2144 | office123                      |    1 | True  | office.n.01|number3
 2164 | ironlady2                      |    9 | True  | iron.n.01|lady.n.01|number1
 2186 | susanita123                    |  361 | True  | fname|pph1|at1|number3
 2208 | woofwoof1234                   |    1 | True  | woof.n.01|woof.n.01|number4
 2211 | sweetie1                       |  117 | True  | sweetheart.n.01|number1
 2220 | alphabet1                      |    1 | True  | alphabet.n.01|number1
 2224 | bigfish111                     |   89 | True  | large.a.01|fish.n.01|number3
 2229 | qwer321ty                      |  433 | False | char1|char3|number3|char2
 2263 | server2009                     |    7 | True  | waiter.n.01|number4
 2292 | packers12                      |   15 | True  | packer.n.01|number2
 2298 | judomaster1                    |    1 | True  | judo.n.01|maestro.n.01|number1
 2305 | overkill17                     |   43 | True  | overkill.n.01|number2
 2307 | slangcell123                   |    1 | True  | slang.n.01|cell.n.01|number3
 2311 | studio123                      |    1 | True  | studio.n.01|number3
 2316 | 123456toast                    |    1 | True  | number6|toast.n.01
 2334 | milksoap23                     |   21 | True  | milk.n.01|soap.n.01|number2
 2336 | solder123                      |    1 | True  | solder.n.01|number3
 2343 | 12345678asdf                   |   41 | False | number8|char4
 2355 | newfuture@09                   |  161 | True  | new.a.01|future.n.01|special1|number2
 2362 | angels2009                     |   39 | True  | angel.n.01|number4
 2369 | jasmine2                       |    7 | True  | jasmine.n.01|number1
 2381 | 1992friendship                 |   69 | True  | number4|friendship.n.01
 2383 | german22                       |   45 | True  | german.a.01|number2
 2393 | missyou55                      |  213 | True  | miss.v.01|ppy|number2
 2418 | realbeing2                     |   17 | True  | real.a.01|being.n.01|number1
 2419 | missled10                      |  421 | True  | miss.v.01|lead.v.01|number2
 2421 | siteadmin1                     |   93 | True  | site.n.01|nn1|number1
 2426 | womanology2                    |    9 | True  | woman.n.01|ology.n.01|number1
 2429 | makan12345                     |   83 | False | char5|number5
 2441 | justhack1                      |    1 | True  | merely.r.01|hack.n.01|number1
 2443 | hamburger1                     |    3 | True  | hamburger.n.01|number1
 2453 | kindrat123                     |    1 | True  | kind.n.01|rat.n.01|number3
 2475 | google001                      |  627 | True  | np|number3
 2478 | spank_123                      |    5 | True  | spank.v.01|special1|number3
 2512 | 169forum                       |  403 | True  | number3|forum.n.01
 2524 | slavco2009                     |  173 | True  | slav.a.01|char2|number4
 2570 | gateway4                       |    9 | True  | gateway.n.01|number1
 2573 | pretender4u                    |  397 | True  | pretender.n.01|number1|char1
 2600 | angel110                       |   61 | True  | angel.n.01|number3
 2603 | papamama1                      |  233 | True  | dad.n.01|ma.n.01|number1
 2608 | master1984                     |   21 | True  | maestro.n.01|number4
 2649 | computer33                     |   59 | True  | computer.n.01|number2
 2657 | nonsense.                      |    5 | True  | nonsense.n.01|special1
 2659 | viruschat2                     |    9 | True  | virus.n.01|chat.n.01|number1
 2665 | genie111                       |   19 | True  | genie.n.01|number3
 2694 | thai1992                       |   57 | True  | thai.a.01|number4
 2706 | gogreen1                       |    1 | True  | travel.v.01|green.s.01|number1
 2711 | housesink40                    |  325 | True  | house.n.01|sink.n.01|number2
 2717 | bubbles123                     |    1 | True  | bubble.n.01|number3
 2757 | 6starfoods                     |  281 | True  | number1|star.n.01|food.n.01
 2768 | videoline2009                  |    5 | True  | video.n.01|line.n.01|number4
 2774 | protect12                      |    1 | True  | protect.v.01|number2
 2785 | foundation0                    |    5 | True  | foundation.n.01|number1
 2793 | ison1234                       |    5 | True  | be.v.01|ii|number4
 2813 | 2002jeep                       |   79 | True  | number4|jeep.n.01
 2834 | radio4forlife                  |   33 | True  | radio.n.01|number1|if|life.n.01
 2841 | counter09051987                |  285 | True  | counter.n.01|number8
 2863 | goodnews9                      |   29 | True  | good.a.01|news.n.01|number1
 2880 | arsenal4                       |    9 | True  | arsenal.n.01|number1
 2905 | apple123456789                 |    1 | True  | apple.n.01|number9
 2925 | manman521                      |  349 | True  | man.n.01|man.n.01|number3
 2935 | muevasion123                   |  257 | True  | char2|evasion.n.01|number3
 2946 | loveu123                       |   53 | True  | love.n.01|char1|number3
 2959 | growing1                       |    1 | True  | growing.a.01|number1
 2988 | genius_90                      |  513 | True  | genius.n.01|special1|number2
 2999 | piano123                       |    1 | True  | piano.n.01|number3
 3073 | 4notrust                       |  125 | True  | number1|at|trust.n.01
 3076 | coldspy123                     |    1 | True  | cold.a.01|spy.n.01|number3
 3079 | 1234genti                      |    1 | True  | number4|gent.n.01|ppis1
 3088 | online007                      |    3 | True  | on-line.a.01|number3
 3100 | weed1234                       |    1 | True  | weed.n.01|number4
 3102 | notleftyet1                    |    1 | True  | xx|leave.v.01|yet.r.01|number1
 3105 | epsilon25                      |   47 | True  | epsilon.n.01|number2
 3121 | incognito2008                  |    3 | True  | incognito.r.01|number4
 3128 | nemesis75                      |  585 | True  | nemesis.n.01|number2
 3151 | cool1111                       |   33 | True  | cool.a.01|number4
 3163 | hummingbirds1                  |   37 | True  | hummingbird.n.01|number1
 3168 | 123456789paulo                 |  531 | True  | number9|mname
 3174 | starwars29                     |  629 | True  | star.n.01|war.n.01|number2
 3233 | symbol33                       |   57 | True  | symbol.n.01|number2
 3257 | webhost67                      |  293 | True  | web.n.01|host.n.01|number2
 3263 | designer456                    |   27 | True  | interior_designer.n.01|number3
 3270 | pebbles7                       |   35 | True  | pebble.n.01|number1
 3283 | anous11111                     |   37 | True  | at1|nous.n.01|number5
 3286 | sarajevo2008                   |  770 | True  | city|number4
 3290 | delta1994                      |   63 | True  | delta.n.01|number4
 3317 | truster08                      |  189 | True  | trust.n.01|char2|number2
 3321 | iloveyou30                     |  297 | True  | ppis1|love.v.01|ppy|number2
 3326 | smartguy123                    |    1 | True  | smart.a.01|guy.n.01|number3
 3334 | canallita12                    |    1 | True  | can.v.01|db|pph1|at1|number2
 3341 | helpme09                       |    5 | True  | help.v.01|ppio1|number2
 3346 | rich9999                       |  167 | True  | rich.a.01|number4
 3350 | linuxwin77                     |  113 | True  | linux.n.01|win.n.01|number2
 3366 | airfile*1                      |   41 | True  | air.n.01|file.n.01|special1|number1
 3372 | cocoapuff1                     |    1 | True  | cocoa.n.01|puff.n.01|number1
 3378 | creator2                       |  877 | True  | godhead.n.01|number1
 3389 | fake2000                       |  203 | True  | bogus.s.01|number4
 3400 | deadlove3                      |   13 | True  | dead.a.01|love.n.01|number1
 3420 | asdfghjkl123456789             |   81 | False | char4|char2|char3|number9
 3429 | idream79                       |  525 | True  | ppis1|dream.n.01|number2
 3447 | pornsite1                      |    1 | True  | pornography.n.01|site.n.01|number1
 3473 | meandyou1                      |    1 | True  | ppio1|cc|ppy|number1
 3484 | psychic1                       |    1 | True  | psychic.s.01|number1
 3487 | aitor105                       |  425 | True  | at1|pph1|cc|number3
 3490 | 123456hobby                    |    1 | True  | number6|avocation.n.01
 3492 | tan123456                      |    1 | True  | tan.s.01|number6
 3497 | jajanbatik11                   |   65 | True  | char2|january.n.01|batik.n.01|number2
 3515 | comics2008                     |    3 | True  | comic_strip.n.01|number4
 3520 | joeissexy1                     |   41 | True  | mname|be.v.01|sexy.a.01|number1
 3537 | neverd0that                    |  249 | True  | never.r.01|char1|number1|cst
 3548 | november.3                     |  373 | True  | november.n.01|special1|number1
 3549 | deadmeat8                      |   37 | True  | dead.a.01|meat.n.01|number1
 3557 | neverlose777                   |   45 | True  | never.r.01|lose.v.01|number3
 3584 | braves10                       |  347 | True  | brave.n.01|number2
 3591 | redgin00                       |   41 | True  | red.s.01|gin.n.01|number2
 3615 | 123456angel                    |    1 | True  | number6|angel.n.01
 3668 | memorysafe2                    |    9 | True  | memory.n.01|safe.n.01|number1
 3690 | server09                       |    5 | True  | waiter.n.01|number2
 3709 | keep3210                       |  147 | True  | keep.v.01|number4
 3714 | 100mychemical                  |   33 | True  | number3|appge|chemical.a.01
 3724 | wildan99                       |  481 | True  | wild.a.01|at1|number2
 3749 | love4metal                     |   37 | True  | love.n.01|number1|metallic_element.n.01
 3762 | windows40                      |  153 | True  | windows.n.01|number2
 3816 | 11yeahbaby                     |  979 | True  | number2|uh|baby.n.01
 3831 | muslim1984                     |   17 | True  | muslim.a.01|number4
 3833 | loveran123                     |   25 | True  | lover.n.01|at1|number3
 3845 | explorer3                      |    7 | True  | explorer.n.01|number1
 3855 | cornet**                       |    1 | True  | cornet.n.01|special2
 3864 | asad123456                     |    1 | True  | at1|sad.a.01|number6
 3873 | webhost9                       |   29 | True  | web.n.01|host.n.01|number1
 3880 | freemoney10                    |   17 | True  | free.a.01|money.n.01|number2
 3882 | 123456abcdefg                  |    1 | True  | char1|run.v.01|number1|char3|number1
 3894 | handsome123                    |  243 | True  | fine-looking.s.01|number3
 3910 | arsenal09                      |    3 | True  | arsenal.n.01|number2
 3940 | dairyman88                     |   87 | True  | dairyman.n.01|number2
 3946 | mindBend1                      |  333 | True  | mind.n.01|bend.v.01|number1
 3954 | webcam1!                       |    1 | True  | webcam.n.01|number1|special1
 3957 | komit123                       |  377 | True  | char3|pph1|number3
 3958 | mymaster24                     |  105 | True  | appge|maestro.n.01|number2
 3962 | pulpufiction2                  |  841 | True  | pulp.n.01|char1|fiction.n.01|number1
 3994 | pass4sure                      |   37 | True  | pass.v.01|number1|certain.a.02
 4001 | shahid123                      |  285 | True  | np1|number3
 4013 | gravity82                      |  175 | True  | gravity.n.01|number2
 4022 | 786editorial                   |  123 | True  | number3|editorial.a.01
 4027 | junior88                       |   61 | True  | junior.a.01|number2
 4053 | 123456789asdf                  |  179 | False | number9|char4
 4060 | brave999                       |   19 | True  | brave.a.01|number3
 4080 | landers9                       |   47 | True  | lander.n.01|number1
 4084 | amstaff1                       |    5 | True  | be.v.01|staff.n.01|number1
 4085 | memet123                       |    1 | True  | ppio1|meet.v.01|number3
 4088 | formula_1                      |    5 | True  | formula.n.01|special1|number1
 4092 | beat1009                       |  161 | True  | beat.n.01|number4
 4099 | edge020202                     |   93 | True  | edge.n.01|number6
 4103 | cmand100                       |  361 | True  | nnu|cc|number3
 4106 | hoteyes21                      |   49 | True  | hot.a.01|eyes.n.01|number2
 4112 | onepiece12                     |    1 | True  | mc1|piece.n.01|number2
 4156 | idream56                       |  413 | True  | ppis1|dream.n.01|number2
 4212 | ahmed12345                     |   79 | True  | mname|number5
 4224 | bijounasset1                   |   97 | True  | bijou.n.01|char1|asset.n.01|number1
 4228 | blowme69                       |  101 | True  | blow.n.01|ppio1|number2
 4238 | gatelband123                   |   41 | True  | gate.n.01|nnu|cc|number3
 4253 | gshop2008                      |  109 | True  | char1|shop.n.01|number4
 4265 | oceanocean2                    |    9 | True  | ocean.n.01|ocean.n.01|number1
 4270 | art4u123                       |  649 | True  | art.n.01|number1|char1|number3
 4288 | jason2009                      |  459 | True  | mname|number4
 4296 | windows101                     |   43 | True  | windows.n.01|number2
 4297 | games4free                     |   53 | True  | game.n.01|number1|free.a.01
 4300 | option2009                     |    5 | True  | option.n.01|number4
 4307 | resbox123                      |  497 | True  | char3|box.n.01|number3
 4308 | innocent123                    |    1 | True  | innocent.a.01|number3
 4320 | 3comhome                       |  105 | True  | number1|char3|home.n.01
 4337 | changed911                     |  299 | True  | change.v.01|number3
 4362 | playnet01                      |   17 | True  | play.v.01|net.a.01|number2
 4387 | thejack2009                    |    1 | True  | at|mname|number4
 4396 | pasha939                       |  925 | True  | pasha.n.01|number3
 4484 | wysiwyg27                      |   75 | True  | wysiwyg.a.01|number2
 4491 | tennis123                      |    1 | True  | tennis.n.01|number3
 4515 | realist67                      |  171 | True  | realist.n.01|number2
 4603 | alienchat88                    |  269 | True  | alien.s.01|chat.n.01|number2
 4607 | mystery29                      |  103 | True  | mystery.n.01|number2
 4624 | zigzag08                       |   21 | True  | zigzag.n.01|number2
 4656 | adminwarrior1                  |    1 | True  | nn1|warrior.n.01|number1
 4688 | breakit1                       |   17 | True  | interruption.n.02|pph1|number1
 4690 | predate3                       |   19 | True  | predate.v.01|number1
 4708 | david2009                      |    5 | True  | mname|number4
 4749 | mypassword5                    |   29 | True  | appge|password.n.01|number1
 4757 | revival1                       |    1 | True  | revival.n.01|number1
 4762 | advocate9                      |   15 | True  | advocate.n.01|number1
 4769 | web654321                      |   19 | True  | web.n.01|number6
 4785 | road2hell                      |    9 | True  | road.n.01|number1|hell.n.01
 4806 | penisface1                     |    1 | True  | penis.n.01|face.n.01|number1
 4817 | hamster29                      |   65 | True  | hamster.n.01|number2
 4820 | polarbear1                     |    1 | True  | polar.s.01|bear.n.01|number1
 4830 | verify84                       |  205 | True  | verify.v.01|number2
 4841 | cameraman22                    |   41 | True  | cameraman.n.01|number2
 4891 | libido123                      |    1 | True  | libido.n.01|number3
 4899 | magentaboy55                   |  177 | True  | magenta.n.01|male_child.n.01|number2
 4924 | uhood123456                    |  101 | True  | char1|hood.n.01|number6
 4992 | samurai185                     |  513 | True  | samurai.n.01|number3
 4994 | icecurtain02                   |   41 | True  | ice.n.01|curtain.n.01|number2
```

---

*解析說明：359 筆由 log parser 擷取；官方 header 統計為 367 筆（差異 8 筆來自 log 格式邊界案例）。破解密碼列表以 log 解析資料為準。*
