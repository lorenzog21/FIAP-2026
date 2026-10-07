/*
 * AgroSmart - Fase 6: simulacao de sensores (TinkerCad / Arduino Uno)
 *
 * Le 4 grandezas do talhao e imprime uma linha CSV na Serial a cada
 * INTERVALO_MS. O formato espelha o schema de data/bronze/sensores/*.json
 * gerado por ingest.py:
 *   talhao_id,t_ms,umidade_solo_pct,temperatura_c,umidade_ar_pct,luminosidade_pct,irrigacao
 *
 * Ligacoes (TinkerCad):
 *   A0  Sensor de temperatura TMP36 (saida)
 *   A1  Sensor de umidade do solo (saida)
 *   A2  Fotoresistor (LDR) em divisor de tensao com resistor de 10k
 *   A3  Potenciometro 10k -> simula umidade do ar (TinkerCad nao tem DHT)
 *   D8  LED verde  -> sistema ativo
 *   D9  LED vermelho -> alerta de risco fungico
 *   D10 LED azul   -> irrigacao acionada (rele simulado)
 */

const char TALHAO_ID[] = "T1";
const unsigned long INTERVALO_MS = 2000;

const int PIN_TEMP = A0;
const int PIN_SOLO = A1;
const int PIN_LDR = A2;
const int PIN_AR = A3;
const int LED_OK = 8;
const int LED_ALERTA = 9;
const int LED_IRRIGACAO = 10;

// Limiares da regra local (mesma logica do motor de regras em Python)
const float SOLO_MIN_IRRIGAR = 30.0;
const float AR_ALTO = 75.0;
const float TEMP_FAVORAVEL_MIN = 24.0;
const float TEMP_FAVORAVEL_MAX = 32.0;

float lerTemperaturaC() {
  // TMP36: 10 mV/grau, offset de 500 mV
  float tensao = analogRead(PIN_TEMP) * (5.0 / 1023.0);
  return (tensao - 0.5) * 100.0;
}

float lerPercentual(int pino) {
  return analogRead(pino) * (100.0 / 1023.0);
}

void setup() {
  Serial.begin(9600);
  pinMode(LED_OK, OUTPUT);
  pinMode(LED_ALERTA, OUTPUT);
  pinMode(LED_IRRIGACAO, OUTPUT);
  Serial.println("talhao_id,t_ms,umidade_solo_pct,temperatura_c,umidade_ar_pct,luminosidade_pct,irrigacao");
}

void loop() {
  float temperatura = lerTemperaturaC();
  float umidadeSolo = lerPercentual(PIN_SOLO);
  float umidadeAr = lerPercentual(PIN_AR);
  float luminosidade = lerPercentual(PIN_LDR);

  bool irrigar = umidadeSolo < SOLO_MIN_IRRIGAR;
  bool riscoFungico = umidadeAr >= AR_ALTO &&
                      temperatura >= TEMP_FAVORAVEL_MIN &&
                      temperatura <= TEMP_FAVORAVEL_MAX;

  digitalWrite(LED_OK, HIGH);
  digitalWrite(LED_IRRIGACAO, irrigar ? HIGH : LOW);
  digitalWrite(LED_ALERTA, riscoFungico ? HIGH : LOW);

  Serial.print(TALHAO_ID);          Serial.print(",");
  Serial.print(millis());           Serial.print(",");
  Serial.print(umidadeSolo, 1);     Serial.print(",");
  Serial.print(temperatura, 1);     Serial.print(",");
  Serial.print(umidadeAr, 1);       Serial.print(",");
  Serial.print(luminosidade, 1);    Serial.print(",");
  Serial.println(irrigar ? 1 : 0);

  delay(INTERVALO_MS);
}
