### Built With

* <a href="https://www.python.org/">Python</a>
* <a href="https://discord.com/developers/docs/intro">Discord Developer Portal</a>

<!-- PREREQUISITES -->

### Prerequisites

* Python
* Python IDE

### Installation

1. Clone the repo
   ```sh
   git clone git@bitbucket.org:Shahar0080/discord-travel-budget-tracker.git
   ```
2. Client setup:
    1. Move to the client directory
       ```sh
       pip install -r requirements.txt
       ```
    2. Define environment properties as set in the environment variables section below
    3. Run main.py

<!-- ENVIRONMENT VARIABLES -->

### Environment Variables

| **Setting**         | **Description**                                                                                          |
|---------------------|----------------------------------------------------------------------------------------------------------|
| `EXCHANGE_API_KEY`  | API key for exchangerate-api to get currency data.                                                       |
| `DISCORD_BOT_TOKEN` | Token for the discord bot from discord developer portal.                                                 |
| `DATABASE_URL`      | URL for the db, should be in the following format: "postgresql://username:password@server:port/db-name". | 
| `ALLOWED_IDS`       | The allowed user ids, separated by comma (,).                                                            |

<!-- LICENSE -->

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<!-- CONTACT -->

## Contact

[Shahar Azar](https://www.linkedin.com/in/shahar-azar/) - shahar.azar2@gmail.com

[Bitbucket - Discord Travel Budget Tracker](https://bitbucket.org/Shahar0080/discord-travel-budget-tracker/src)
