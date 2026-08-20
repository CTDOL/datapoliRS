const axios = require('axios');
axios.get('http://localhost:8000/api/v1/gabinete/liderancas', {
  headers: {
    // I don't have the token. I can just test the DB query via python script.
  }
}).catch(e => console.log('Cannot fetch API directly without auth'));
