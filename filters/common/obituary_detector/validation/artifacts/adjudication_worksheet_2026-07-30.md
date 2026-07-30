# Owner adjudication worksheet — obituary label boundary (LD#83, 2026-07-30)

Rule (owner-endorsed 2026-06-14): **Block** = fresh obituary/death notice/mourning piece whose PRIMARY purpose is to mark a specific person's recent death. **Keep** = memorial events, anniversary/legacy tributes, laws/programs prompted by a death, profiles of the living, stories merely mentioning death.

For each row: your verdict `block` / `keep` (+ optional note). The 4-model panel drifts broader than the rule; your calls become the label authority for these classes in the next retrain.

## 1. `dutch_news_nu_nl_algemeen_13aa3586170a`
**Kind omgekomen door aanrijding in Bergen op Zoom kort na jaarwisseling**

- Category: fn_delta non-promoted (split)
- Panel: gemini=not_obituary, gemma3=obituary, qwen3=not_obituary, phi4=obituary (majority: split)
- Scores: v3=0.963156 v4=0.878854 v5=0.9868641495704651
- Oracle label in heldout: positive

> Een auto kwam in botsing met een jong kind op de Noordsingel in de Brabantse stad. "Het kind is als gevolg van de aanrijding komen te overlijden", schrijft de politie. De leeftijd van het kind is niet bekend. Een woordvoerder kon NU.nl nog geen details geven over hoe het ongeluk heeft kunnen gebeuren. Er loopt nog een onderzoek. Volgens persbureau ...

**Owner verdict:** _______

## 2. `global_news_spiegel_2933c8e4b736`
**Warburg: 22-Jähriger erschießt Bekannten bei mutmaßlichem Jagdunfall**

- Category: fn_delta non-promoted (split)
- Panel: gemini=not_obituary, gemma3=obituary, qwen3=not_obituary, phi4=obituary (majority: split)
- Scores: v3=0.977094 v4=0.817917 v5=0.9873769283294678
- Oracle label in heldout: positive

> Bei einem mutmaßlichen Jagdunfall ist ein 23-Jähriger in Ostwestfalen von einem Bekannten erschossen worden. Der Mann sei trotz umgehender Wiederbelebungsversuche noch im Wald gestorben, teilten Polizei und Staatsanwaltschaft mit. »Wir gehen derzeit von einem tragischen Jagdunfall aus«, sagte ein Polizeisprecher. Allerdings müssten die genauen Umst...

**Owner verdict:** _______

## 3. `pacific_fiji_times_7b4a4f06a57d`
**House fire in Nakasi claims two lives**

- Category: fn_delta non-promoted (split)
- Panel: gemini=not_obituary, gemma3=obituary, qwen3=not_obituary, phi4=obituary (majority: split)
- Scores: v3=0.992536 v4=0.797438 v5=0.9554618000984192
- Oracle label in heldout: positive

> Two people are believed to have died in a house fire on Matana Street in Nakasi last night. One body has been located at the scene, while efforts are ongoing to locate a second body believed to be within the ruins of the burnt. The fire started around 9pm last night. The house was a double story building. The Fiji Times is seeking additional inform...

**Owner verdict:** _______

## 4. `new_zealand_rnz_468d19cef77c`
**Homicide investigation launched after woman’s death in Clutha**

- Category: fn_delta non-promoted (split)
- Panel: gemini=not_obituary, gemma3=obituary, qwen3=obituary, phi4=not_obituary (majority: split)
- Scores: v3=0.977994 v4=0.760749 v5=0.885819137096405
- Oracle label in heldout: positive

> It comes after a woman died at a Clutha property and a man remains in a critical condition in hospital....

**Owner verdict:** _______

## 5. `new_zealand_stuff_nz_e6fe5544434b`
**Sister says she was in contact with brother in hour before shooting**

- Category: fn_delta non-promoted (split)
- Panel: gemini=obituary, gemma3=obituary, qwen3=not_obituary, phi4=not_obituary (majority: split)
- Scores: v3=0.97555 v4=0.690688 v5=0.9699643850326538
- Oracle label in heldout: positive

> A man has died and three other people are in a critical condition after a shooting at the small settlement on the west coast of the Manawatū region....

**Owner verdict:** _______

## 6. `newsapi_general_849827291def`
**One dead after 2 helicopters crash mid-air in, New Jersey, Hammonton p**

- Category: fn_delta non-promoted (not_obituary)
- Panel: gemini=not_obituary, gemma3=obituary, qwen3=not_obituary, phi4=not_obituary (majority: not_obituary)
- Scores: v3=0.982084 v4=0.227071 v5=0.9564804434776306
- Oracle label in heldout: positive

> At least one person has died and another person was injured after two helicopters collided mid-air....

**Owner verdict:** _______

## 7. `china_taipei_times_1b067f78562b`
**METRO RAMPAGE: Man died trying to stop Taipei stabbing suspect**

- Category: fn_delta non-promoted (not_obituary)
- Panel: gemini=obituary, gemma3=not_obituary, qwen3=not_obituary, phi4=not_obituary (majority: not_obituary)
- Scores: v3=0.986847 v4=0.059148 v5=0.016364609822630882
- Oracle label in heldout: positive

> ...

**Owner verdict:** _______

## 8. `belgian_gazet_van_antwerpen_e54bdbf24b3c`
**Vrienden organiseren muziekfestival ter ere van overleden Filip (47): **

- Category: hard positive, suspected KEEP violation
- Panel: gemini=obituary, gemma3=obituary, qwen3=not_obituary, phi4=obituary (majority: obituary)
- Scores: v3=0.961644 v4=0.824515 v5=0.9585776329040527
- Oracle label in heldout: positive

> Met Filip Fest, een eendaags muziekfestival op 2 mei, willen enkele Rupelmondenaren hun betreurde vriend Filip Van Mieghem eren. De man overleed vorig jaar net voor Kerst, amper anderhalve maand nadat bij hem pancreaskanker werd vastgesteld....

**Owner verdict:** _______

## 9. `french_france_info_politique_42e038b30a44`
**Obsèques de Brigitte Bardot : pourquoi Marine Le Pen sera présente**

- Category: hard positive, suspected KEEP violation
- Panel: gemini=obituary, gemma3=obituary, qwen3=not_obituary, phi4=obituary (majority: obituary)
- Scores: v3=0.98323 v4=0.833986 v5=0.9908671379089355
- Oracle label in heldout: positive

> La cérémonie en hommage à "BB", décédée le 28 décembre à 91 ans, doit débuter à 11 heures à Saint-Tropez. Parmi les invités : plusieurs cadres du RN et peu de membres du gouvernement....

**Owner verdict:** _______

## 10. `dutch_news_ad_algemeen_291bef952b6d`
**Vader die kinderen en buren doodstak in Suriname overleden in cel**

- Category: v4 heldout FP, panel says obituary
- Panel: gemini=obituary, gemma3=obituary, qwen3=obituary, phi4=obituary (majority: obituary)
- Scores: v3=0.998794 v4=0.950298 v5=0.9674007892608643
- Oracle label in heldout: negative

> De man die in de nacht van zaterdag op zondag in Suriname negen mensen zou hebben doodgestoken, onder wie vier van zijn eigen kinderen, heeft in zijn cel zelfmoord gepleegd....

**Owner verdict:** _______

## 11. `portuguese_rtp_noticias_97a95df47263`
**Realizou-se esta quarta-feira o funeral de Brigitte Bardot**

- Category: v4 heldout FP, panel says obituary
- Panel: gemini=obituary, gemma3=obituary, qwen3=obituary, phi4=obituary (majority: obituary)
- Scores: v3=0.999998 v4=0.999961 v5=0.9999654293060303
- Oracle label in heldout: negative

> A cerimónia decorreu em Saint-Tropez. Centenas de admiradores juntaram-se no exterior para o adeus à estrela do cinema francês....

**Owner verdict:** _______

## 12. `belgian_dh_les_sports_1e0556ff9a09`
**”Tu me manques à Manchester” : l’hommage d’Erling Haaland à Kevin De B**

- Category: v4 heldout FP, panel says not_obituary
- Panel: gemini=not_obituary, gemma3=not_obituary, qwen3=not_obituary, phi4=not_obituary (majority: not_obituary)
- Scores: v3=0.992324 v4=0.966494 v5=0.99318528175354
- Oracle label in heldout: negative

> KDB va intégrer le tout nouveau “Hall of Fame” de la Belgique ce dimanche lors de la cérémonie du Soulier d’or. ......

**Owner verdict:** _______

## 13. `british_irish_irish_independent_b765027efc8d`
**‘I miss you every day, Ash’ – Ryan Casey posts tribute to Ashling Murp**

- Category: v4 heldout FP, panel says obituary
- Panel: gemini=not_obituary, gemma3=obituary, qwen3=obituary, phi4=obituary (majority: obituary)
- Scores: v3=0.948367 v4=0.959576 v5=0.9720125198364258
- Oracle label in heldout: negative

> Ashling Murphy’s boyfriend Ryan Casey has posted a tribute to her on the fourth anniversary of her tragic death....

**Owner verdict:** _______

## 14. `british_irish_rte_news_38f2d8adc8ae`
**Murder probe launched following death of man in Co Derry**

- Category: v4 heldout FP, panel says not_obituary
- Panel: gemini=not_obituary, gemma3=not_obituary, qwen3=obituary, phi4=not_obituary (majority: not_obituary)
- Scores: v3=0.996437 v4=0.975582 v5=0.987208902835846
- Oracle label in heldout: negative

> A murder investigation has been launched following the death of a man in Coleraine, Co Derry....

**Owner verdict:** _______
