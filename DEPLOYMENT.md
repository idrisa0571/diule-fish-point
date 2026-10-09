# Kuweka DIULE FISH POINT mtandaoni

Mradi huu una mpangilio wa kupelekwa Render kupitia `render.yaml`.

## Hatua za kuweka mtandaoni

1. Tengeneza repository ya **private** GitHub na upakie mafaili ya mradi. Faili za `instance/` na `*.db` zimeondolewa kwenye Git kwa makusudi; usipakie database yenye taarifa za biashara.
2. Tengeneza PostgreSQL database ya kudumu. Weka connection string yake kwenye Render kama `DATABASE_URL`. Usitumie SQLite kwenye huduma ya mtandaoni, kwa sababu data yake inaweza kupotea huduma ikijengwa upya.
3. Kwenye Render, chagua **New + → Blueprint** kisha unganisha repository hiyo. Blueprint itaweka huduma ya wavuti na `SECRET_KEY` ya kipekee.
4. Wakati Render inapouliza thamani za siri, weka `DATABASE_URL` na `ADMIN_PASSWORD`. `ADMIN_USERNAME` itakuwa `admin` kwa chaguo-msingi. Tumia nenosiri imara na lihifadhi salama.
5. Baada ya deployment kufanikiwa, Render itatoa kiungo cha `*.onrender.com`. Fungua kiungo hicho kwenye simu au kompyuta na uingie kwa username na nenosiri uliloweka.

Database ya mtandaoni huanza tupu; taarifa zilizopo kwenye `instance/database.db` hazihamishwi zenyewe. Hifadhi database hiyo ya hapa salama na panga uhamisho wake kabla ya kutumia mfumo wa mtandaoni kwa biashara.

Huduma ya bure ya Render inaweza kusimama bila matumizi na kuchukua muda kuamka inapofunguliwa tena. Upatikanaji na gharama za PostgreSQL hutegemea mtoa huduma na mpango uliochagua.
