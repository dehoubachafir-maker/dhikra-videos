# Visuels « versets de la nature » → TikTok (5 par jour)

Compte TikTok : maissane4149, via Metricool (blogId 7237953, fuseau Europe/Paris).
Les images sont hébergées dans ce dépôt public (raw.githubusercontent.com) car Metricool a besoin d'une URL publique.

## Lot quotidien (5 images, 1080×1920)
1. Choisir 5 nouveaux passages sur la création / la nature, courts (≤ 2 versets), absents de `used_verses.json`.
2. Récupérer le texte arabe (édition simple avec voyelles) et la traduction française (Hamidullah) sur alquran.cloud
   (`/v1/ayah/S:V/editions/quran-simple,fr.hamidullah`) via WebFetch (le shell n'a pas accès à ces sites).
   Si un texte revient tronqué, ne JAMAIS le compléter de mémoire : choisir un passage plus court.
3. Générateur : `tiktok/generator/make_visuals.py` (PIL + Raqm, police DejaVu Sans Bold qui n'a pas U+06D6 : on retire ce signe de pause).
   Importer ses fonctions (grad, layer, glow_disc, wavy_band, render_card, frame…) et écrire 5 nouvelles scènes (une ambiance par verset), un `verses` JSON,
   puis lancer la génération. Pas de personnage, pas d'être animé en gros plan ; scènes propres, sans formes ambiguës.
4. Vérifier 3 fois AVANT de publier :
   - texte arabe + français comparés à la source A (alquran.cloud) ;
   - texte arabe + français comparés à la source B indépendante (api.quran.com `/api/v4/verses/by_key/S:V?translations=31&fields=text_uthmani,text_imlaei`), comparaison par programme ;
   - contrôle technique des PNG (taille 1080×1920, texte dans le cadre) + relecture visuelle de chaque image (Read), y compris un zoom sur la carte de texte.
5. Pousser les PNG dans `tiktok/AAAA-MM-JJ/` (commit sur main, avec fetch avant), puis programmer 5 posts TikTok (photo) via Metricool
   `createScheduledPost` pour le lendemain à 11 h, 13 h, 15 h, 17 h, 19 h (heures impaires : les vidéos de hadiths du compte sont aux heures paires).
   Légende : traduction + référence, une phrase de contemplation, « Source — texte vérifié trois fois… », hashtags #islam #coran #rappel #création.
6. Mettre à jour `used_verses.json`.

## Règles
- Ne jamais publier un texte non vérifié par les deux sources. En cas de doute : ne pas publier ce visuel et le signaler.
- Écarts de signes entre éditions (soukoun, chadda) : suivre la graphie du mushaf de Médine (quran.com).
