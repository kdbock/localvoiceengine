# Local Voice Engine studio plan

## Purpose

Local Voice Engine turns published or planned Neuse News stories into short-form
video packages. It borrows the production-tracker idea from The Listening Room
and the creator workflow from the Hyper Local creator studio.

The system should help the editor decide which stories deserve video, generate a
clean production brief, create or attach voiceover, organize visuals and track
where each video stands.

## Core Rooms

### Dashboard

Shows the stories most likely to become useful videos today.

Priority signals:

- reader questions
- public safety urgency
- meeting decisions
- business openings
- public records
- school or family utility
- election relevance
- strong Facebook or website performance

### Story Desk

Turns an article into a video package.

Fields:

- headline
- county
- source story URL
- video format
- hook
- 45-second script
- captions
- visual beats
- editor notes
- approval status

### Voice Room

Manages narration choices.

Fields:

- voice provider
- voice profile
- pace
- tone
- pronunciation notes
- final audio file
- disclosure notes when needed

### Visual Room

Plans the background and motion layer.

Reusable visual types:

- map card
- courthouse or city hall card
- public-record card
- business opening card
- timeline card
- quote card
- reader question card
- branded end card

### Library

Stores completed and draft packages.

Filters:

- date
- county
- format
- platform
- status
- reporter
- topic

### Analytics

Tracks performance after publishing.

Metrics:

- views
- average watch time
- shares
- comments
- saves
- follower growth
- website clicks
- revenue when available

## Statuses

- idea
- drafted
- needs editor review
- approved
- voiced
- visuals ready
- exported
- posted
- needs follow-up

## First Build

1. Generate production briefs from article text.
2. Add Qwen voice generation.
3. Add a simple local dashboard.
4. Add reusable templates for the top seven Neuse News video formats.
5. Add a manual analytics tracker.

## Editorial Guardrails

- Follow AP style.
- Use sentence-style headlines.
- Attribute claims clearly.
- Avoid speculation.
- Avoid dramatic treatment of crime.
- Keep election content neutral and consistent.
- Require human approval before publishing sensitive stories.
