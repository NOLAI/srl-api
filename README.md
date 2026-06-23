# SRL API

The SRL API is the backend for the self-regulated learning (SRL) dashboard. It supplies the dashboard with essay sessions, questionnaire responses, learning-process timelines, and product-goal progress.

The frontend is maintained in the separate `srl-dashboard` repository. It provides the user interface for selecting essays and visualising cognitive and metacognitive processes, completed goals, and questionnaire responses.

## Features

The API provides:

- Moodle user lookup by username;
- essay-session listings for each user;
- Moodle questionnaire responses;
- cognitive and metacognitive process timelines;
- model-derived writing processes;
- progress towards essay product goals; and
- scheduled batch processing of essays and writing processes.

## Processing pipeline

### Learning processes

Trace labels stored in the essay database are mapped to cognitive, metacognitive, and other learning processes. Consecutive occurrences of the same process are combined into timeline entries for display in the dashboard.

Writing activity can also be classified from saved essay revisions. The classifier uses features derived from:

- revision segmentation;
- LIWC analysis through the Receptiviti API;
- T-Scan linguistic analysis;
- semantic similarity to Moodle course pages using Dutch spaCy embeddings; and
- the bundled XGBoost model.

The XGBoost model and related writing-process generation code were created for:

Bistolfi, I., de Mooij, S., van der Graaf, J., & Molenaar, I. (2025). Towards real-time automated self-regulated learning detection in essays. In A. I. Cristea, E. Walker, L. Yu, O. C. Santos, & S. Isotani (Eds.), _Artificial Intelligence in Education. AIED 2025_ (Lecture Notes in Computer Science, Vol. 15879). Springer, Cham. <https://doi.org/10.1007/978-3-031-98420-4_27>

### Product goals

The product-goal processor evaluates saved essay versions against course-specific definitions. It reports progress in three areas:

- essay structure;
- paragraph relevance; and
- coverage of the required main points.

The processor supports English and Dutch text using spaCy language models.

### Questionnaire responses

Questionnaire metadata and responses are read from Moodle. Supported response types include Boolean values, free text, single choice, multiple choice, and ranked choice.

## Technology

The application is built with:

- Python 3.12;
- FastAPI and Uvicorn;
- Tortoise ORM with MySQL;
- pandas, NumPy, scikit-learn, and XGBoost;
- spaCy and langdetect; and
- Docker and cron for deployment and scheduled processing.

## Requirements

Running the complete application requires:

- a MySQL database containing essay, trace, writing-process, and product-goal data;
- a Moodle MySQL database containing the referenced user, course, page, and questionnaire tables;
- access credentials for the T-Scan API;
- access credentials for the Receptiviti LIWC API; and
- local course configuration files in `DATA_DIR`.

The application expects the database schemas to exist already. It does not create or migrate them.

## Local development

Create the local environment file:

```sh
cp .env.example .env
```

After configuring `.env` and populating `DATA_DIR`, build and start the development container:

```sh
docker compose -f docker-compose.dev.yml up --build
```

The development configuration exposes:

- the API at <http://localhost/>;
- interactive API documentation at <http://localhost/docs>; and
- phpMyAdmin at <http://localhost:81/>.

The Compose configuration mounts `./data` at `/data`. Set `DATA_DIR=/data` when using this configuration.

## Configuration

The API uses the following environment variables:

| Variable                       | Description                                         |
| ------------------------------ | --------------------------------------------------- |
| `DB_FLORA_ANNOTATION`          | Essay database name                                 |
| `DB_FLORA_ANNOTATION_USER`     | Essay database user                                 |
| `DB_FLORA_ANNOTATION_PASSWORD` | Essay database password                             |
| `DB_FLORA_ANNOTATION_HOST`     | Essay database host                                 |
| `DB_FLORA_ANNOTATION_PORT`     | Essay database port                                 |
| `DB_MOODLE`                    | Moodle database name                                |
| `DB_MOODLE_USER`               | Moodle database user                                |
| `DB_MOODLE_PASSWORD`           | Moodle database password                            |
| `DB_MOODLE_HOST`               | Moodle database host                                |
| `DB_MOODLE_PORT`               | Moodle database port                                |
| `DATA_DIR`                     | Directory containing local JSON configuration files |
| `TSCAN_API_URL`                | T-Scan API base URL                                 |
| `TSCAN_API_USERNAME`           | T-Scan API username                                 |
| `TSCAN_API_PASSWORD`           | T-Scan API password                                 |
| `LIWC_API_URL`                 | Receptiviti API base URL                            |
| `LIWC_API_KEY`                 | Receptiviti API key                                 |
| `LIWC_API_SECRET`              | Receptiviti API secret                              |

### Local data files

`DATA_DIR` may contain the following deployment-specific files:

| File                         | Description                                                      |
| ---------------------------- | ---------------------------------------------------------------- |
| `goals.json`                 | Course-specific product-goal definitions in English and/or Dutch |
| `course_questionnaires.json` | Mapping from course IDs to questionnaire IDs                     |
| `ignored_courses.json`       | Course IDs omitted from essay listings                           |

Example versions of these files are available in `data/examples`.

## Docker

The Docker image runs the API with Uvicorn on port 88 and starts cron for scheduled processing:

```sh
docker build -t srl-api .
```

The container expects the environment variables and `DATA_DIR` files described above.

## API endpoints

| Method and path                          | Description                                               |
| ---------------------------------------- | --------------------------------------------------------- |
| `GET /api/user/{username}`               | Look up a Moodle user                                     |
| `GET /api/essay/list/{user_id}`          | List essay sessions for a user                            |
| `GET /api/questions/{id}`                | Return configured questionnaire responses for a user      |
| `GET /api/process/{user_id}/{course_id}` | Return the learning-process timeline for an essay session |
| `GET /api/goals/{user_id}/{course_id}`   | Return product-goal progress for an essay session         |
| `GET /api/process/process`               | Run writing-process batch processing                      |
| `GET /api/goals/process`                 | Run product-goal batch processing                         |

Request and response details are available through FastAPI's generated `/docs` endpoint while the application is running.

## Scheduled processing

The container starts cron alongside the API. The supplied crontab invokes:

- product-goal processing every day at 01:00; and
- writing-process classification every day at 02:00.

The jobs call the API's batch-processing endpoints from within the container. Times use the container's configured timezone.
