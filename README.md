# ApiScript

ApiScript is a declarative programming language for creating 
stateless Web APIs with ease. The syntax is built around
HTTP verbs and paths and it allows very easily describing an API.

In ApiScript a function is basically an API endpoint, which 
is described by a HTTP verb, route and implmentation.

A simple hello world program looks like this:

```
GET / => "Hello World!";
```

The meaning of which is to expose the string content `"Hello World!"`
for all requests that match the `GET /` routing pattern.


## Stateless by design

Being stateless simplfies API development and makes it API infinitely scalable.
This allows a simple delcarative syntax where the implementation can be done
using a series of pipes. This also makes it trivial to parallelize.

Basically each endpoint is implemented by a pipeline. The request is piped 
through operators which modify the response content.

```
GET /users => select users(id,name) | limit 10 | format json
```


## Bultin ORM

State still needs to be stored somewhere for useful APIs, in ApiScripts's case
state management is completely delegated to databases/external services.

Within the language is possible to form queries using the operators which 
will be translated to a query.

```
table users {                                       // CREATE TABLE users (
    id: pk int;                                     //     id INT PRIMARY KEY,
    name: str;                                      //     name VARCHAR,
    password: str;                                  //     password VARCHAR,
    is_organisation_admin: bool;                    //     is_organisation_admin BOOL,
    is_database_admin: bool;                        //     is_database_admin BOOL)
}                  

GET /users => 
    // SELECT users.id, users.name, users.is_organisation_admin, users.is_database_admin, organisations.id, organisations.name
    // FROM users INNER JOIN organisations ON users.organisation = organisations.id;
    select users(id, name, is_organisation_admin, is_database_admin, organisation(id, name)) | format json;
```


## Ready for Web (development)

Declare a few routes and get a web server up and running ready for development
purposes in a few minutes. 

```
GET / => "<a href='version'>version</a><br/><a href='hello'>hello</a>";

GET /hello => "Hello World!";

GET /version => "1.0";
```
