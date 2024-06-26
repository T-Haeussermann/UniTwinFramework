mongosh admin -u dt -p dt
use digitalTwins;
db.createUser(
  { user: "dt", pwd: "dt",
    roles: [ { role: "readWrite", db: "digitalTwins" }]
  }
);