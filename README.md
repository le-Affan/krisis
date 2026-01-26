# Krisis

**Krisis** is an A/B experimentation framework for machine learning models.

It routes live traffic between two model variants, collects delayed numeric outcomes,
and reports statistically grounded evidence to support human decision-making.

## What it does
- Registers two competing ML models
- Splits incoming requests between them
- Logs predictions with stable request IDs
- Ingests delayed numeric outcomes
- Computes difference with confidence intervals

## Status
MVP under development.  

## Core idea
**The system reports evidence. Humans decide.**
