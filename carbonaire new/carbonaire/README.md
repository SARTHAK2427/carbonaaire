# Carbonaire — Rule-Based Carbon Footprint Expert System

## Project Structure

```
carbonaire/
│
├── core/
│   ├── emission_factors.py      # All EF constants (edit to update factors)
│   ├── input_schema.py          # Input data model & validation
│   ├── scope1_calculator.py     # Scope 1 (direct fuel) calculations
│   ├── scope2_calculator.py     # Scope 2 (electricity) calculations
│   ├── scope3_calculator.py     # Scope 3 (value chain) calculations
│   └── master_calculator.py     # Aggregates all scopes → total CO2e
│
├── rules/
│   ├── rule_engine.py           # Fires rules against calculated emissions
│   ├── scope1_rules.py          # Rules & thresholds for Scope 1
│   ├── scope2_rules.py          # Rules & thresholds for Scope 2
│   └── scope3_rules.py          # Rules & thresholds for Scope 3
│
├── benchmarks/
│   ├── industry_benchmark.py    # Indian IT SME benchmarks (BRSR-derived)
│   └── company_benchmark.py     # Placeholder for real company data (future)
│
├── utils/
│   ├── report_generator.py      # Formats final output report / insights
│   └── helpers.py               # Shared utility functions
│
├── tests/
│   ├── test_calculators.py      # Unit tests for all calculators
│   ├── test_rules.py            # Unit tests for rule engine
│   └── test_integration.py      # End-to-end integration test
│
├── main.py                      # CLI entry point — run & test the system
└── README.md
```

## How to Run

```bash
# Run the interactive CLI (enter your data manually)
python main.py

# Run a pre-built sample scenario (no input needed — good for testing)
python main.py --demo

# Run all unit tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_calculators.py -v
```

## How to Extend

| What you want to do | File to edit |
|---|---|
| Add a new fuel type | `core/emission_factors.py` → `SCOPE1_FACTORS` |
| Add a new state's grid EF | `core/emission_factors.py` → `STATE_GRID_EF` |
| Change performance band thresholds | `benchmarks/industry_benchmark.py` |
| Add a new insight/recommendation rule | `rules/scope1_rules.py` (or scope2/3) |
| Add a new input field | `core/input_schema.py` |
| Plug in real company benchmark data | `benchmarks/company_benchmark.py` |

## Dependencies

```bash
pip install tabulate colorama pytest
```
