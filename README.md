## Executar Ambiente - Virtual Env

```bash
source .venv/bin/activate
```

```
Dica: se renomear/mover o projeto de novo, rode rm -rf .venv && uv sync para regenerar.
```

## Run agent

```
adk run .
```

```
adk run agents/meu_agente2
```

```
adk web ./agents
```

## Adicionar dependencia

```
uv add "sqlalchemy==2.0.51"
```

## Resert DB

```
 uv run python -m db.reset
```
