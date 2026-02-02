# Market Experiment

A double auction market experiment demonstrating how decentralized decisions with private information lead to market equilibrium.

## Deployment Options

### Option 1: Self-Hosted (with nginx)

Run on your own server behind nginx.

```bash
# As root on your server
git clone https://github.com/eivindhammers/otree-market-experiment.git /opt/otree-market-experiment
cd /opt/otree-market-experiment
bash deploy/setup.sh
```

Then:
1. Edit `/etc/systemd/system/otree.service` - set `OTREE_ADMIN_PASSWORD`
2. Edit `deploy/nginx.conf` - replace `experiment.yourdomain.com` with your domain
3. Copy nginx config: `cp deploy/nginx.conf /etc/nginx/sites-available/otree`
4. Enable site: `ln -s /etc/nginx/sites-available/otree /etc/nginx/sites-enabled/`
5. Start services:
   ```bash
   systemctl daemon-reload
   systemctl enable otree
   systemctl start otree
   systemctl reload nginx
   ```

### Option 2: Railway

1. Create account at https://railway.app
2. New project → Deploy from GitHub → select this repo
3. Add PostgreSQL database (New → Database → PostgreSQL)
4. Set environment variables:
   ```
   OTREE_ADMIN_PASSWORD=your_secure_password
   OTREE_SECRET_KEY=your_random_secret_key
   OTREE_PRODUCTION=1
   ```
5. Deploy

## Running the Experiment

1. Go to `https://yourdomain.com/admin` (or your Railway URL)
2. Login with username `admin` and your password
3. Create session → "Market Experiment" → set 60-70 participants
4. Share the session link with students

### Using Rooms (Recommended for Class)

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
