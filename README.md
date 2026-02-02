# Market Experiment

A double auction market experiment demonstrating how decentralized decisions with private information lead to market equilibrium.

## Deploy to Railway

1. **Create a Railway account** at https://railway.app

2. **Create a new project** from this GitHub repository

3. **Add a PostgreSQL database**:
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will automatically set the DATABASE_URL

4. **Set environment variables** (in Settings → Variables):
   ```
   OTREE_ADMIN_PASSWORD=your_secure_password
   OTREE_SECRET_KEY=your_random_secret_key
   OTREE_PRODUCTION=1
   ```

5. **Deploy** - Railway will automatically detect the Procfile and deploy

## Running the Experiment

1. Access your Railway URL (e.g., `https://your-app.up.railway.app`)

2. Go to the admin interface: `https://your-app.up.railway.app/admin`
   - Login with username `admin` and your OTREE_ADMIN_PASSWORD

3. Create a new session:
   - Select "Market Experiment"
   - Set number of participants (60-70 for your class)

4. Share the session-wide link with students, or use the "Rooms" feature

## Using Rooms (Recommended for Class)

The experiment includes a pre-configured room called "econ_class":

1. In admin, go to "Rooms" → "econ_class"
2. Share the room URL with students
3. Students join and wait
4. You create a session from the room when ready

## Local Development

```bash
pip install -r requirements.txt
otree devserver
```

Visit http://localhost:8000

## Experiment Design

- **Participants**: Split into buyers and sellers
- **Buyers**: Receive private values (how much the good is worth to them)
- **Sellers**: Receive private costs (how much it costs them to produce)
- **Trading**: Call market - everyone submits bids/asks, market clears
- **Result**: Shows supply/demand curves and how market finds equilibrium

The experiment runs for 3 rounds to demonstrate convergence.
