# Entrega 2 — Coleta de dados do ambiente (IoT / simulação)

Código: [`iot/agrosmart_sensores/agrosmart_sensores.ino`](../iot/agrosmart_sensores/agrosmart_sensores.ino)

## Sensores utilizados

| Grandeza | Componente no TinkerCad | Pino | Conversão no código |
|---|---|---|---|
| Temperatura (°C) | Sensor de temperatura **TMP36** | A0 | `(V - 0,5) × 100` |
| Umidade do solo (%) | **Sensor de umidade do solo** | A1 | `leitura × 100 / 1023` |
| Luminosidade (%) | **Fotoresistor (LDR)** + resistor 10 kΩ (divisor de tensão) | A2 | `leitura × 100 / 1023` |
| Umidade do ar (%) | **Potenciômetro** 10 kΩ | A3 | `leitura × 100 / 1023` |

> O TinkerCad não possui sensor DHT11/DHT22. A umidade do ar é, portanto, **simulada com um potenciômetro** (girar = variar a umidade). Isso é declarado na entrega e no vídeo.

Atuadores/eventos simulados (regras locais do Arduino, as mesmas do motor de regras em Python):

| LED | Pino | Acende quando |
|---|---|---|
| Verde | D8 | sistema ativo |
| Vermelho | D9 | umidade do ar ≥ 75% **e** temperatura entre 24 e 32 °C (condição favorável ao fungo) |
| Azul | D10 | umidade do solo < 30% (irrigação acionada — relé simulado) |

LEDs precisam de resistor de 220 Ω em série.

## Passo a passo no TinkerCad (≈ 20 min)

1. Em [tinkercad.com/circuits](https://www.tinkercad.com/circuits), **Create → Circuit**.
2. Adicione: 1 × Arduino Uno R3, 1 × TMP36, 1 × Soil Moisture Sensor, 1 × Photoresistor, 1 × Potentiometer, 3 × LED (verde, vermelho, azul), 4 × resistor (3 × 220 Ω, 1 × 10 kΩ), 1 × protoboard pequena.
3. Ligações:
   - **TMP36:** pino esquerdo → 5V; pino direito → GND; pino central → **A0**.
   - **Umidade do solo:** VCC → 5V; GND → GND; saída (sinal) → **A1**.
   - **LDR:** um terminal → 5V; outro terminal → **A2** e, no mesmo nó, resistor de 10 kΩ → GND.
   - **Potenciômetro:** extremos → 5V e GND; terminal central → **A3**.
   - **LEDs:** ânodo (perna longa) → resistor 220 Ω → **D8 / D9 / D10**; cátodo → GND.
4. Clique em **Code → Text**, apague o conteúdo e cole o `.ino`.
5. **Start Simulation**, abra o **Serial Monitor**. Clique em cada sensor durante a simulação e mexa nos controles (temperatura, umidade do solo, luz, potenciômetro) para gerar variação e acender os LEDs.
6. Para o print de evidência, capture a tela com o circuito, o Serial Monitor com várias linhas e ao menos um LED aceso.

## Prints a entregar (salvar em `entrega/prints/`)

- [ ] `tinkercad_circuito.png` — circuito completo montado
- [ ] `tinkercad_serial.png` — Serial Monitor com as linhas CSV
- [ ] `tinkercad_alerta.png` — LED vermelho ou azul aceso (evento simulado)

Inclua também o link público do circuito (**Share → Invite people / link**), se possível.

## Exemplo de dados gerados (Serial)

```csv
talhao_id,t_ms,umidade_solo_pct,temperatura_c,umidade_ar_pct,luminosidade_pct,irrigacao
T1,2000,52.3,25.1,81.4,67.2,0
T1,4000,51.9,25.4,82.0,66.8,0
T1,6000,28.7,27.9,83.6,12.1,1
T1,8000,27.5,30.2,85.2,9.4,1
```

Mesmo schema de `data/bronze/sensores/batch_*/sensor_T*.json` (`ingest.py`), acrescido do campo `t_ms` (tempo desde o boot) e do estado `irrigacao`.

## Como o simulador Python se relaciona com o TinkerCad

O TinkerCad não expõe a Serial para fora do navegador, então o pipeline **não** lê o circuito diretamente. `ingest.py` gera leituras com o **mesmo schema e as mesmas grandezas**, em 4 talhões com cenários distintos (equilibrado, úmido/quente, seco, evento de chuva), com ~5% de falhas de sensor propositais para exercitar a validação. O circuito demonstra o hardware; o simulador alimenta a análise com volume de dados suficiente.
