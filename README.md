# Izklopi Elektro Primorska

Home Assistant integracija, ki spremlja [načrtovane izklope električne energije](https://elektro-primorska.si/izklopi/) za poljubno lokacijo na območju **Elektra Primorska** in jih objavi kot senzorje.

## Kako deluje

Integracija periodično (privzeto vsakih 30 minut) prenese seznam napovedanih izklopov in ga filtrira glede na nastavljena **kraj** in **hišno številko**. Ustvari tri entitete:

| Entiteta | Opis |
|---|---|
| `sensor.…_naslednji_izpad` | Časovni žig začetka naslednjega izklopa (`device_class: timestamp`), oziroma `unknown`, če izklopa ni. Atributi: kraj, ulica, hišne številke, čas konca, tip akcije, število prihajajočih izklopov in njihov seznam (do 10). |
| `sensor.…_konec_izpada` | Čas konca istega izklopa. |
| `binary_sensor.…_izpad_v_teku` | `ON`, ko smo trenutno znotraj termina izklopa (`od ≤ zdaj ≤ do`), sicer `OFF` (`device_class: problem`). Stanje se preklopi točno ob uri začetka oziroma konca izklopa. |

Podrobnosti iskanja:

- Kraj se ujema s podnizom v imenu kraja ali ulice.
- Hišna številka se primerja točno s seznamom prizadetih številk (npr. `1` ne ustreza `10`).
- Izklopi brez seznama hišnih številk se upoštevajo vedno, saj običajno prizadenejo celotno območje.

## Namestitev

### HACS (priporočeno)

1. V HACS dodaj ta repozitorij kot *Custom repository* (vrsta: Integration).
2. Poišči **Izklopi Elektro Primorska** in ga namesti.
3. Ponovno zaženi Home Assistant.

### Ročno

1. Kopiraj mapo `custom_components/izklopi_elektro_primorska` v `custom_components/` svoje Home Assistant namestitve.
2. Ponovno zaženi Home Assistant.

## Nastavitev

Nastavitve → Naprave in storitve → Dodaj integracijo → **Izklopi Elektro Primorska**:

| Polje | Opis |
|---|---|
| Kraj | Npr. `Osp`. Ujema se s krajem ali imenom ulice. |
| Hišna številka | Neobvezno, npr. `1` ali `1000 a`. Če je prazno, se upoštevajo vsi izklopi za kraj. |
| Območje | Nadzorništvo Elektra Primorska (privzeto vsa). |
| Interval posodabljanja | Minute med osvežitvami (privzeto 30). |

Nastavitve lahko kadarkoli spremeniš prek **Reconfigure** na kartici integracije.

## Primeri avtomatizacij

V vseh primerih `sensor.VAS_SENZOR_naslednji_izpad` zamenjaj s svojim senzorjem
novo napovedjo (npr. `sensor.elektro_izpadi_osp_22_a_naslednji_izpad`).

### Obvestilo ob novem izklopu

```yaml
alias: Obvestilo o izklopu elektrike
triggers:
  - trigger: state
    entity_id: sensor.VAS_SENZOR_naslednji_izpad
actions:
  - action: notify.mobile_app
    data:
      title: "Načrtovan izklop elektrike"
      message: >
        {{ state_attr(trigger.entity_id, 'ulica') }},
        {{ state_attr(trigger.entity_id, 'kraj') }}:
        od {{ states(trigger.entity_id) }}
        do {{ state_attr(trigger.entity_id, 'konec') }}
```

### TTS odštevanje pred izpadom

Vsako minuto preveri napovedi in 45, 30, 15 ter 5 minut pred začetkom izpada
izgovori napoved prek izbranih zvočnikov:

```yaml
alias: TTS odštevanje pred izpadom
triggers:
  - trigger: time_pattern
    minutes: "/1"
variables:
  izpad: >-
    {% set napovedi = state_attr('sensor.VAS_SENZOR_naslednji_izpad', 'naslednji_izpadi') or [] %}
    {% set ns = namespace(najdi=none, minute=0) %}
    {% for o in napovedi %}
      {% if ns.najdi is none and o.od %}
        {% set razlika = (as_timestamp(o.od) - as_timestamp(now())) / 60 %}
        {% set zaokrozeno = razlika | round(0) | int %}
        {% if zaokrozeno in [45, 30, 15, 5] %}
          {% set ns.najdi = o %}
          {% set ns.minute = zaokrozeno %}
        {% endif %}
      {% endif %}
    {% endfor %}
    {{ {'izpad': ns.najdi, 'minute': ns.minute} | to_json }}
conditions:
  - condition: template
    value_template: "{{ izpad.izpad is not none }}"
actions:
  - action: tts.microsoft_say
    data:
      cache: false
      entity_id: media_player.VAS_ZVOCNIK
      message: >-
        Pozor. Čez {{ izpad.minute }} minut se začne napovedani izklop elektrike
        na naslovu {{ izpad.izpad.ulica }}, {{ izpad.izpad.kraj }}.
mode: single
```

### Varnostno zapiranje ob izpadu

Obstoječi varnostni avtomatizaciji (npr. zapiranje senčnikov ali pergole ob
vetru/dežju) lahko dodaš trigger, ki jo sproži največ 1 uro pred začetkom
izpada:

```yaml
- trigger: template
  id: elektro_izklop
  value_template: >-
    {% set napovedi = state_attr('sensor.VAS_SENZOR_naslednji_izpad', 'naslednji_izpadi') or [] %}
    {% set zdaj = as_timestamp(now()) %}
    {% set ns = namespace(zapri=false) %}
    {% for o in napovedi %}
      {% if o.od %}
        {% set razlika = as_timestamp(o.od) - zdaj %}
        {% if razlika <= 3600 and razlika > 0 %}{% set ns.zapri = true %}{% endif %}
      {% endif %}
    {% endfor %}
    {{ ns.zapri }}
```

### Izklop avtomatik med izpadom

Avtomatizacija, ki izklopi izbrane nadzorne avtomatike (npr. sončno sledenje
senčnikov/pergole) 1 h 5 min pred začetkom izpada in jih 1 h po koncu spet
vklopi. Je idempotentna — vsako minuto uskladi stanje, zato prenese tudi
spremembe ali preklic napovedi:

```yaml
alias: Izklop avtomatik med izpadom
triggers:
  - trigger: time_pattern
    minutes: "/1"
  - trigger: state
    entity_id: sensor.VAS_SENZOR_naslednji_izpad
variables:
  okno: >-
    {% set napovedi = state_attr('sensor.VAS_SENZOR_naslednji_izpad', 'naslednji_izpadi') or [] %}
    {% set zdaj = as_timestamp(now()) %}
    {% set ns = namespace(okno=false) %}
    {% for o in napovedi %}
      {% if o.od and o.do %}
        {% if zdaj >= as_timestamp(o.od) - 3900 and zdaj <= as_timestamp(o.do) + 3600 %}
          {% set ns.okno = true %}
        {% endif %}
      {% endif %}
    {% endfor %}
    {{ ns.okno }}
actions:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ okno == true }}"
          - condition: template
            value_template: "{{ expand(['automation.VASA_AVTOMATIKA']) | selectattr('state', 'eq', 'on') | list | count > 0 }}"
        sequence:
          - action: automation.turn_off
            target:
              entity_id:
                - automation.VASA_AVTOMATIKA # <- zamenjaj s svojimi
      - conditions:
          - condition: template
            value_template: "{{ okno == false }}"
          - condition: template
            value_template: "{{ expand(['automation.VASA_AVTOMATIKA']) | selectattr('state', 'ne', 'on') | list | count > 0 }}"
        sequence:
          - action: automation.turn_on
            target:
              entity_id:
                - automation.VASA_AVTOMATIKA # <- zamenjaj s svojimi
mode: single
```

> **Pozor:** če varnostno zapiranje (npr. pergole) deluje posredno prek druge
> avtomatizacije, poskrbi, da ta izvajalec ostane vklopljen, ali pa varnostni
> avtomatizaciji dodaj neposreden ukaz na `cover`.

## Opombe

- Deluje samo za območje distributerja **Elektro Primorska d.d.**
- Podatki so neuradni; vir je spletna stran elektro-primorska.si.
- Integracija ne shranjuje zgodovine — senzorji vedno odražajo trenutno napovedane izklope.
- Težave in predlogi: [GitHub Issues](https://github.com/Cyber-Wolfy17/izklopi-elektro-primorska/issues).

## Licenca

[MIT](LICENSE)
