//
// read this
// https://nodejs.org/api/https.html
// https://node-postgres.com/features/queries
// https://hackernoon.com/https-medium-com-amanhimself-converting-a-buffer-to-json-and-utf8-strings-in-nodejs-2150b1e3de57
// https://stackoverflow.com/questions/17836438/getting-binary-content-in-node-js-with-http-request
//

/*
 1.
 в этой файле созданы пара функций которые работают по очереди
 первая get_stocks запрашивает списов акций 
 тут можно прочесть описание функции https://iextrading.com/developer/docs/#symbols

 get_stocks функция вызывает вторую функцию и передает ей все собранные акции


 2. работа с базой
 https://node-postgres.com/


 чтобы запустить проект нужно скопировать из Excel One drive user pass.
 и в командной строке запустить node stock-load.js

 программа будет загружать недостоющие данные из интернета.
 программу можно всегда прервать и запустить заново.

*/
const https = require('https');
const sleep = require('sleep');
const { Client } = require('pg')

const url_symbosl = 'https://api.iextrading.com/1.0/ref-data/symbols'

function get_stocks(callback) {
    https.get(url_symbosl, (resp) => {
        var data = []
        var str = ''
        // date event - means that we start to recieve the data
        resp.on('data', (d) => {
            // variable d is data chunk.
            // we collect them into array
            data.push(d);
        }).on('end', (d) => {
            // concat all buffers into one.
            let full_buffer = Buffer.concat(data)
            // convert into string
            str = full_buffer.toString()
            // print the lenght
            console.log(str.length);
            // print the first 2000 symbols
            console.log(str.substr(0, 100));
            // convert into object
            obj = JSON.parse(str)

            callback(obj);
        });
    });
}

function show_stats(stocks) {

    // we take first five stocks
    var few_stocks = stocks.slice(0, 4);
    console.log('total symbols', stocks.length);
    few_stocks.forEach(st => {
        console.log(st.symbol, st.name, st.date, st.isEnabled, st.type, st.iexId);
    });

    var stats = {
        'max_name_len': 0,
        'max_name': '',
        'max_symbol_length': 0,
        'max_symbol': '',
        'max_type_length': 0,
        'max_type': ''
    }

    stocks.forEach((el) => {

        if (el.symbol.length > stats.max_symbol_length) {
            stats.max_symbol_length = el.symbol.length;
            stats.max_symbol = el.symbol;
        }

        if (el.name.length > stats.max_name_len) {
            stats.max_name_len = el.name.length;
            stats.max_name = el.name;
        }

        if (el.type.length > stats.max_type_length) {
            stats.max_type_length = el.type.length;
            stats.max_type = el.type;
        }
    });
}

function get_connection() {
    const client = new Client({
        user: '', // DB user
        host: '' , //DB host
        database: '', // DB dbname
        password: '', // DB Pass
        port: 5432,
    });
    return client;
}

function filter_stocks(web_data, db_data) {
    var ret = []
    var match = 0
    web_data.forEach((x) => {
        if (!db_data[x.symbol]) {
            ret.push(x);
        } else{
            match ++;
        }
    });

    console.log('from', web_data.length, 'found', match);
    console.log(ret.length, 'to save!');

    return ret;
}

function query_stocks(callback) {
    let client = get_connection();
    client.connect();
    var ret = {}
    // we not include the sid field in insert query because it's auto increment
    const select = 'select symbol, sid from public.stocks;';
    client.query(select, (err, res) => {
        if (err) {
            console.log(err.stack)
        } else {
            res.rows.forEach((x) => {
                ret[x.symbol] = x.sid
            });

            callback(ret)
            client.end()
        }
    });
}

function save_data(stocks) {
    let client = get_connection();
    client.connect();

    // we not include the sid field in insert query because it's auto increment
    const insert_query = 'INSERT INTO public.stocks(symbol, date, name, is_enabled, type, ref_id, ref_type_id) VALUES ($1, $2, $3, $4, $5, $6, 1) RETURNING sid'
    console.log('start inserting');
    fun = ['|', '/', '~', '\\']
    left = stocks.length
    c = 0
    stocks.forEach((s) => {
        client.query(insert_query, [s.symbol, new Date(s.date), s.name, s.isEnabled, s.type, s.iexId], (err, res) => {
            if (err) {
                console.log(err.stack)
            } else {
                console.log(fun[(c++) % fun.length], left--);
            }
        })
    })
}

// get stocks from the web
get_stocks((data) => {

    // get the stocks from database
    query_stocks((db_data) => {
        // show some stats about loaded stocks
        show_stats(data);
        data_to_save = filter_stocks(data, db_data);
        console.log(data_to_save.length);
        save_data(data_to_save);
    })
});