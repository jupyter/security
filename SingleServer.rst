About This Document
===================

This document was created November 2021 as part of a `Trusted CI engagement <https://blog.trustedci.org/2021/08/engagement-with-jupyter.html>`_ .
The intent was to review existing documentation for single-server JupyterHub
deployments with a focus on security-related instructions, and suggest modifications
and additions to help users secure their Jupyter deployment on a single-server system.
These instructions should not be confused with documentation for `The Littlest
JupyterHub <https://tljh.jupyter.org>`_ . 

=============================================
Applicable Jupyter Notebook Security Settings
=============================================

Authentication and Users
========================

This section was originally copied from https://jupyterhub.readthedocs.io/en/latest/getting-started/authenticators-users-basics.html

Authentication and User Basics
------------------------------

The default Authenticator uses `PAM
<https://en.wikipedia.org/wiki/Pluggable_authentication_module>`_ to authenticate system users with
their username and password. With the default Authenticator, any user
with an account and password on the system will be allowed to login.

Create a set of allowed users
*****************************

You can restrict which users are allowed to login with a set,
``Authenticator.allowed_users``:

.. code-block:: python

    c.Authenticator.allowed_users = {'mal', 'zoe', 'inara', 'kaylee'}

Users in the ``allowed_users`` set are added to the Hub database when the Hub is
started.

Configure admins (``admin_users``)
********************************

.. note::

    As of JupyterHub 2.0, the full permissions of ``admin_users`` should not
    be required.  Instead, you can assign `roles
    <https://jupyterhub.readthedocs.io/en/latest/rbac/roles.html>`_ to users
    or groups with only the scopes they require.

Admin users of JupyterHub, ``admin_users``, can add and remove users from
the user ``allowed_users`` set. ``admin_users`` can take actions on other users'
behalf, such as stopping and restarting their servers.

A set of initial admin users, ``admin_users`` can be configured as follows:

.. code-block:: python

    c.Authenticator.admin_users = {'mal', 'zoe'}

Users in the admin set are automatically added to the user ``allowed_users`` set,
if they are not already present.

Each authenticator may have different ways of determining whether a user is an
administrator. By default JupyterHub uses the PAMAuthenticator which provides the
``admin_groups`` option and can set administrator status based on a user
group. For example we can let any user in the ``wheel`` group be admin:



.. code-block:: python

    c.PAMAuthenticator.admin_groups = {'wheel'}


Give admin access to other users' notebook servers (``admin_access``)
*******************************************************************

Since the default ``JupyterHub.admin_access`` setting is ``False``, the admins
do not have permission to log in to the single user notebook servers
owned by *other users*. If ``JupyterHub.admin_access`` is set to ``True``,
then admins have permission to log in *as other users* on their
respective machines, for debugging. **As a courtesy, you should make
sure your users know if admin_access is enabled.**

Add or remove users from the Hub
********************************

Users can be added to and removed from the Hub via either the admin
panel or the REST API. When a user is **added**, the user will be
automatically added to the ``allowed_users`` set and database. Restarting the Hub
will not require manually updating the ``allowed_users`` set in your config file,
as the users will be loaded from the database.

After starting the Hub once, it is not sufficient to **remove** a user
from the allowed users set in your config file. You must also remove the user
from the Hub's database, either by deleting the user from JupyterHub's
admin page, or you can clear the ``jupyterhub.sqlite`` database and start
fresh.

Use LocalAuthenticator to create system users
*********************************************

The ``LocalAuthenticator`` is a special kind of authenticator that has
the ability to manage users on the local system. When you try to add a
new user to the Hub, a ``LocalAuthenticator`` will check if the user
already exists. If you set the configuration value, ``create_system_users``,
to ``True`` in the configuration file, the ``LocalAuthenticator`` has
the privileges to add users to the system. The setting in the config
file is:

.. code-block:: python

    c.LocalAuthenticator.create_system_users = True

Adding a user to the Hub that doesn't already exist on the system will
result in the Hub creating that user via the system ``adduser`` command
line tool. This option is typically used on hosted deployments of
JupyterHub, to avoid the need to manually create all your users before
launching the service. This approach is not recommended when running
JupyterHub in situations where JupyterHub users map directly onto the
system's UNIX users

Use OAuthenticator to support OAuth with popular service providers
******************************************************************

JupyterHub's `OAuthenticator
<https://github.com/jupyterhub/oauthenticator>`_ currently supports the
following popular services:

- Auth0
- Azure AD
- Bitbucket
- CILogon
- GitHub
- GitLab
- Globus
- Google
- MediaWiki
- Okpy
- OpenShift

A generic implementation, which you can use for OAuth authentication
with any provider, is also available.

Use DummyAuthenticator for testing
**********************************

The ``DummyAuthenticator`` is a simple authenticator that
allows for any username/password unless a global password has been set. If
set, it will allow for any username as long as the correct password is provided.
To set a global password, add this to the config file:

.. code-block:: python

    c.DummyAuthenticator.password = "some_password"

Enabling Encryption
===================

Direct Proxy Access or Web Server Frontend
------------------------------------

The section below was originally copied from https://jupyterhub.readthedocs.io/en/stable/reference/technical-overview.html

By default, the **Proxy** listens on all public interfaces on port 8000.
Thus you can reach JupyterHub through either:

- ``http://localhost:8000``
- or any other public IP or domain pointing to your system.

In their default configuration, the other services, the **Hub** and
**Single-User Notebook Servers**, all communicate with each other on localhost
only.

By default, starting JupyterHub will write two files to disk in the current
working directory:

- ``jupyterhub.sqlite`` is the SQLite database containing all of the state of the
  **Hub**. This file allows the **Hub** to remember which users are running and
  where, as well as storing other information enabling you to restart parts of
  JupyterHub separately. It is important to note that this database contains
  **no** sensitive information other than **Hub** usernames.
- ``jupyterhub_cookie_secret`` is the encryption key used for securing cookies.
  This file needs to persist so that a **Hub** server restart will avoid
  invalidating cookies. Conversely, deleting this file and restarting the server
  effectively invalidates all login cookies. The cookie secret file is discussed
  in the `Cookie Secret section of the Security Settings document <../getting-started/security-basics.md>`_ .

The location of these files can be specified via configuration settings. It is
recommended that these files be stored in standard UNIX filesystem locations,
such as ``/etc/jupyterhub`` for all configuration files and ``/srv/jupyterhub`` for
all security and runtime files.

Direct Jupyter Proxy Encryption
*******************************

The section below was originally copied from https://jupyterhub.readthedocs.io/en/latest/getting-started/security-basics.html

Since JupyterHub includes authentication and allows arbitrary code execution,
you should not run it without SSL (HTTPS).

Using an SSL certificate
************************

This will require you to obtain an official, trusted SSL certificate or create a
self-signed certificate. Once you have obtained and installed a key and
certificate you need to specify their locations in the ``jupyterhub_config.py``
configuration file as follows:

.. code-block:: python

    c.JupyterHub.ssl_key = '/path/to/my.key'
    c.JupyterHub.ssl_cert = '/path/to/my.cert'


Some cert files also contain the key, in which case only the cert is needed. It
is important that these files be put in a secure location on your server, where
they are not readable by regular users.

If you are using a **chain certificate**, see also chained certificate for SSL
in the JupyterHub `Troubleshooting FAQ <../troubleshooting.html>`_.

Using letsencrypt
*****************

It is also possible to use `letsencrypt <https://letsencrypt.org/>`_ to obtain
a free, trusted SSL certificate. If you run letsencrypt using the default
options, the needed configuration is (replace ``mydomain.tld`` by your fully
qualified domain name):

.. code-block:: python

    c.JupyterHub.ssl_key = '/etc/letsencrypt/live/{mydomain.tld}/privkey.pem'
    c.JupyterHub.ssl_cert = '/etc/letsencrypt/live/{mydomain.tld}/fullchain.pem'

If the fully qualified domain name (FQDN) is ``example.com``, the following
would be the needed configuration:

.. code-block:: python

    c.JupyterHub.ssl_key = '/etc/letsencrypt/live/example.com/privkey.pem'
    c.JupyterHub.ssl_cert = '/etc/letsencrypt/live/example.com/fullchain.pem'


Web Server Encryption
*********************

Other Internal Encryption
*************************

The section below was originally copied from https://jupyterhub.readthedocs.io/en/stable/reference/websecurity.html

Encrypt internal connections with SSL/TLS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, all communication on the server, between the proxy, hub, and single
-user notebooks is performed unencrypted. Setting the `internal_ssl` flag in
`jupyterhub_config.py` secures the aforementioned routes. Turning this
feature on does require that the enabled `Spawner` can use the certificates
generated by the `Hub` (the default `LocalProcessSpawner` can, for instance).

It is also important to note that this encryption **does not** (yet) cover the
`zmq tcp` sockets between the Notebook client and kernel. While users cannot
submit arbitrary commands to another user's kernel, they can bind to these
sockets and listen. When serving untrusted users, this eavesdropping can be
mitigated by setting `KernelManager.transport` to `ipc`. This applies standard
Unix permissions to the communication sockets thereby restricting
communication to the socket owner. The `internal_ssl` option will eventually
extend to securing the `tcp` sockets as well.

The section below was originally copied from https://jupyterhub.readthedocs.io/en/stable/reference/spawners.html

Communication between the `Proxy`, `Hub`, and `Notebook` can be secured by
turning on `internal_ssl` in `jupyterhub_config.py`. For a custom spawner to
utilize these certs, there are two methods of interest on the base `Spawner`
class: `.create_certs` and `.move_certs`.

The first method, `.create_certs` will sign a key-cert pair using an internally
trusted authority for notebooks. During this process, `.create_certs` can
apply `ip` and `dns` name information to the cert via an `alt_names` `kwarg`.
This is used for certificate authentication (verification). Without proper
verification, the `Notebook` will be unable to communicate with the `Hub` and
vice versa when `internal_ssl` is enabled. For example, given a deployment
using the `DockerSpawner` which will start containers with `ips` from the
`docker` subnet pool, the `DockerSpawner` would need to instead choose a
container `ip` prior to starting and pass that to `.create_certs` (TODO: edit).

In general though, this method will not need to be changed and the default
`ip`/`dns` (localhost) info will suffice.

When `.create_certs` is run, it will `.create_certs` in a default, central
location specified by `c.JupyterHub.internal_certs_location`. For `Spawners`
that need access to these certs elsewhere (i.e. on another host altogether),
the `.move_certs` method can be overridden to move the certs appropriately.
Again, using `DockerSpawner` as an example, this would entail moving certs
to a directory that will get mounted into the container this spawner starts.

Other Jupyter Encryption Settings
===========================

Proxy authentication token
--------------------------

The section below was originally copied from https://jupyterhub.readthedocs.io/en/latest/getting-started/security-basics.html

The Hub authenticates its requests to the Proxy using a secret token that
the Hub and Proxy agree upon. Note that this applies to the default
``ConfigurableHTTPProxy`` implementation. Not all proxy implementations
use an auth token.

The value of this token should be a random string (for example, generated by
``openssl rand -hex 32``). You can store it in the configuration file or an
environment variable

Generating and storing token in the configuration file
******************************************************

You can set the value in the configuration file, ``jupyterhub_config.py``:

.. code-block:: python

    c.ConfigurableHTTPProxy.api_token = 'abc123...' # any random string

Generating and storing as an environment variable
*************************************************

You can pass this value of the proxy authentication token to the Hub and Proxy
using the ``CONFIGPROXY_AUTH_TOKEN`` environment variable:

.. code-block:: bash

    export CONFIGPROXY_AUTH_TOKEN=$(openssl rand -hex 32)

This environment variable needs to be visible to the Hub and Proxy.

Default if token is not set
***************************

If you don't set the Proxy authentication token, the Hub will generate a random
key itself, which means that any time you restart the Hub you **must also
restart the Proxy**. If the proxy is a subprocess of the Hub, this should happen
automatically (this is the default configuration).

.. _cookie-secret:

Cookie secret
-------------

The section below was originally copied from https://jupyterhub.readthedocs.io/en/latest/getting-started/security-basics.html

The cookie secret is an encryption key, used to encrypt the browser cookies
which are used for authentication. Three common methods are described for
generating and configuring the cookie secret.

Generating and storing as a cookie secret file
**********************************************

The cookie secret should be 32 random bytes, encoded as hex, and is typically
stored in a ``jupyterhub_cookie_secret`` file. An example command to generate the
``jupyterhub_cookie_secret`` file is:

.. code-block:: bash

    openssl rand -hex 32 > /srv/jupyterhub/jupyterhub_cookie_secret

In most deployments of JupyterHub, you should point this to a secure location on
the file system, such as ``/srv/jupyterhub/jupyterhub_cookie_secret``.

The location of the ``jupyterhub_cookie_secret`` file can be specified in the
``jupyterhub_config.py`` file as follows:

.. code-block:: python

    c.JupyterHub.cookie_secret_file = '/srv/jupyterhub/jupyterhub_cookie_secret'

If the cookie secret file doesn't exist when the Hub starts, a new cookie
secret is generated and stored in the file. The file must not be readable by
``group`` or ``other`` or the server won't start. The recommended permissions
for the cookie secret file are ``600`` (owner-only rw).

Generating and storing as an environment variable
*************************************************

If you would like to avoid the need for files, the value can be loaded in the
Hub process from the ``JPY_COOKIE_SECRET`` environment variable, which is a
hex-encoded string. You can set it this way:

.. code-block:: bash

    export JPY_COOKIE_SECRET=$(openssl rand -hex 32)

For security reasons, this environment variable should only be visible to the
Hub. If you set it dynamically as above, all users will be logged out each time
the Hub starts.

Generating and storing as a binary string
******************************************

You can also set the cookie secret in the configuration file
itself, ``jupyterhub_config.py``, as a binary string:

.. code-block:: python

    c.JupyterHub.cookie_secret = bytes.fromhex('64 CHAR HEX STRING')


.. important::

   If the cookie secret value changes for the Hub, all single-user notebook
   servers must also be restarted.

Protecting Users
================

The section below was copied originally from https://jupyterhub.readthedocs.io/en/stable/reference/websecurity.html

Semi-trusted and untrusted users
--------------------------------

JupyterHub is designed to be a *simple multi-user server for modestly sized
groups* of **semi-trusted** users. While the design reflects serving semi-trusted
users, JupyterHub is not necessarily unsuitable for serving **untrusted** users.

Using JupyterHub with **untrusted** users does mean more work by the
administrator. Much care is required to secure a Hub, with extra caution on
protecting users from each other as the Hub is serving untrusted users.

One aspect of JupyterHub's *design simplicity* for **semi-trusted** users is that
the Hub and single-user servers are placed in a *single domain*, behind a
*`proxy <https://github.com/jupyterhub/configurable-http-proxy>`_* . If the Hub is serving untrusted
users, many of the web's cross-site protections are not applied between
single-user servers and the Hub, or between single-user servers and each
other, since browsers see the whole thing (proxy, Hub, and single user
servers) as a single website (i.e. single domain).

Protect users from each other
-----------------------------

To protect users from each other, a user must **never** be able to write arbitrary
HTML and serve it to another user on the Hub's domain. JupyterHub's
authentication setup prevents a user writing arbitrary HTML and serving it to
another user because only the owner of a given single-user notebook server is
allowed to view user-authored pages served by the given single-user notebook
server.

To protect all users from each other, JupyterHub administrators must
ensure that:

- A user **does not have permission** to modify their single-user notebook server,
  including:
  - A user **may not** install new packages in the Python environment that runs
    their single-user server.
  - If the `PATH` is used to resolve the single-user executable (instead of
    using an absolute path), a user **may not** create new files in any `PATH`
    directory that precedes the directory containing `jupyterhub-singleuser`.
  - A user may not modify environment variables (e.g. PATH, PYTHONPATH) for
    their single-user server.
- A user **may not** modify the configuration of the notebook server
  (the `~/.jupyter` or `JUPYTER_CONFIG_DIR` directory).

If any additional services are run on the same domain as the Hub, the services
**must never** display user-authored HTML that is neither _sanitized_ nor _sandboxed_
(e.g. IFramed) to any user that lacks authentication as the author of a file.

Mitigate security issues
------------------------

Several approaches to mitigating these issues with configuration
options provided by JupyterHub include:

Enable subdomains
*****************

One aspect of JupyterHub's *design simplicity* for **semi-trusted** users is that
the Hub and single-user servers are placed in a *single domain*, behind a
*`proxy <https://github.com/jupyterhub/configurable-http-proxy>`_* .
If the Hub is serving untrusted
users, many of the web's cross-site protections are not applied between
single-user servers and the Hub, or between single-user servers and each
other, since browsers see the whole thing (proxy, Hub, and single user
servers) as a single website (i.e. single domain).JupyterHub provides the ability to run single-user servers on their own
subdomains. This means the cross-origin protections between servers has the
desired effect, and user servers and the Hub are protected from each other. A
user's single-user server will be at `username.jupyter.mydomain.com`. This also
requires all user subdomains to point to the same address, which is most easily
accomplished with wildcard DNS. Since this spreads the service across multiple
domains, you will need wildcard SSL, as well. Unfortunately, for many
institutional domains, wildcard DNS and SSL are not available. **If you do plan
to serve untrusted users, enabling subdomains is highly encouraged**, as it
resolves the cross-site issues.

Disable user config
-------------------

If subdomains are not available or not desirable, JupyterHub provides a
configuration option `Spawner.disable_user_config`, which can be set to prevent
the user-owned configuration files from being loaded. After implementing this
option, PATHs and package installation and PATHs are the other things that the
admin must enforce.

Prevent spawners from evaluating shell configuration files
----------------------------------------------------------

For most Spawners, `PATH` is not something users can influence, but care should
be taken to ensure that the Spawner does *not* evaluate shell configuration
files prior to launching the server.

Isolate packages using virtualenv
---------------------------------

Package isolation is most easily handled by running the single-user server in
a virtualenv with disabled system-site-packages. The user should not have
permission to install packages into this environment.

It is important to note that the control over the environment only affects the
single-user server, and not the environment(s) in which the user's kernel(s)
may run. Installing additional packages in the kernel environment does not
pose additional risk to the web application's security.

Vulnerability Reporting
================

This section was originally copied from https://jupyterhub.readthedocs.io/en/stable/reference/websecurity.html

If you believe you’ve found a security vulnerability in JupyterHub, or any
Jupyter project, please report it to
`security@ipython.org <mailto:security@iypthon.org>`_ . If you prefer to encrypt
your security reports, you can use `this PGP public
key <https://jupyter-notebook.readthedocs.io/en/stable/_downloads/ipython_security.asc>`_ .

General Security Practices
=============================

The section below was originally copied from https://jupyterhub.readthedocs.io/en/stable/reference/websecurity.html

Security audits
---------------

We recommend that you do periodic reviews of your deployment's security. It's
good practice to keep JupyterHub, configurable-http-proxy, and nodejs
versions up to date.

A handy website for testing your deployment is
`Qualsys' SSL analyzer tool <https://www.ssllabs.com/ssltest/analyze.html>`_ .


Running JupyterHub without Root Privileges
==============================================

The section below was originally copied from https://jupyterhub.readthedocs.io/en/stable/reference/config-sudo.html

**Note:** Setting up `sudo` permissions involves many pieces of system
configuration. It is quite easy to get wrong and very difficult to debug.
Only do this if you are very sure you must.

Overview
--------

There are many Authenticators and Spawners available for JupyterHub. Some, such
as DockerSpawner or OAuthenticator, do not need any elevated permissions. This
document describes how to get the full default behavior of JupyterHub while
running notebook servers as real system users on a shared system without
running the Hub itself as root.

Since JupyterHub needs to spawn processes as other users, the simplest way
is to run it as root, spawning user servers with `setuid <http://linux.die.net/man/2/setuid>`_ .
But this isn't especially safe, because you have a process running on the
public web as root.

A **more prudent way** to run the server while preserving functionality is to
create a dedicated user with `sudo` access restricted to launching and
monitoring single-user servers.

Create a user
-------------

To do this, first create a user that will run the Hub:

.. code-block:: bash

    sudo useradd rhea


This user shouldn't have a login shell or password (possible with -r).

Set up sudospawner
------------------

Next, you will need `sudospawner <https://github.com/jupyter/sudospawner>`_ 
to enable monitoring the single-user servers with sudo:

.. code-block:: bash

    sudo python3 -m pip install sudospawner


Now we have to configure sudo to allow the Hub user (`rhea`) to launch
the sudospawner script on behalf of our hub users (here `zoe` and `wash`).
We want to confine these permissions to only what we really need.

Edit `/etc/sudoers`
-------------------

To do this we add to `/etc/sudoers` (use `visudo` for safe editing of sudoers):

- specify the list of users `JUPYTER_USERS` for whom `rhea` can spawn servers
- set the command `JUPYTER_CMD` that `rhea` can execute on behalf of users
- give `rhea` permission to run `JUPYTER_CMD` on behalf of `JUPYTER_USERS`
  without entering a password

For example:

.. code-block:: bash

    # comma-separated list of users that can spawn single-user servers
    # this should include all of your Hub users
    Runas_Alias JUPYTER_USERS = rhea, zoe, wash
    # the command(s) the Hub can run on behalf of the above users without needing a password
    # the exact path may differ, depending on how sudospawner was installed
    Cmnd_Alias JUPYTER_CMD = /usr/local/bin/sudospawner

    # actually give the Hub user permission to run the above command on behalf
    # of the above users without prompting for a password
    rhea ALL=(JUPYTER_USERS) NOPASSWD:JUPYTER_CMD


It might be useful to modify `secure_path` to add commands in path.

As an alternative to adding every user to the `/etc/sudoers` file, you can
use a group in the last line above, instead of `JUPYTER_USERS`:

.. code-block:: bash

    rhea ALL=(%jupyterhub) NOPASSWD:JUPYTER_CMD


If the `jupyterhub` group exists, there will be no need to edit `/etc/sudoers`
again. A new user will gain access to the application when added to the group:

.. code-block:: bash

    $ adduser -G jupyterhub newuser


Test `sudo` setup
-----------------

Test that the new user doesn't need to enter a password to run the sudospawner
command.

This should prompt for your password to switch to rhea, but _not_ prompt for
any password for the second switch. It should show some help output about
logging options:

.. code-block:: bash

    $ sudo -u rhea sudo -n -u $USER /usr/local/bin/sudospawner --help
    Usage: /usr/local/bin/sudospawner [OPTIONS]

    Options:

    --help          show this help information
    ...


And this should fail:

.. code-block:: bash

    $ sudo -u rhea sudo -n -u $USER echo 'fail'
    sudo: a password is required

Enable PAM for non-root
-----------------------

By default, `PAM authentication <http://en.wikipedia.org/wiki/Pluggable_authentication_module>`_ 
is used by JupyterHub. To use PAM, the process may need to be able to read
the shadow password database.

Shadow group (Linux)
********************

**Note:** On Fedora based distributions there is no clear way to configure
the PAM database to allow sufficient access for authenticating with the target user's password
from JupyterHub. As a workaround we recommend use an
`alternative authentication method <https://github.com/jupyterhub/jupyterhub/wiki/Authenticators>`_ .

.. code-block:: bash

    $ ls -l /etc/shadow
    -rw-r-----  1 root shadow   2197 Jul 21 13:41 shadow


If there's already a shadow group, you are set. If its permissions are more like:

.. code-block:: bash

    $ ls -l /etc/shadow
    -rw-------  1 root wheel   2197 Jul 21 13:41 shadow


Then you may want to add a shadow group, and make the shadow file group-readable:

.. code-block:: bash

    $ sudo groupadd shadow
    $ sudo chgrp shadow /etc/shadow
    $ sudo chmod g+r /etc/shadow


We want our new user to be able to read the shadow passwords, so add it to the shadow group:

.. code-block:: bash

    $ sudo usermod -a -G shadow rhea


If you want jupyterhub to serve pages on a restricted port (such as port 80 for http),
then you will need to give `node` permission to do so:

.. code-block:: bash

    sudo setcap 'cap_net_bind_service=+ep' /usr/bin/node


However, you may want to further understand the consequences of this.

You may also be interested in limiting the amount of CPU any process can use
on your server. `cpulimit` is a useful tool that is available for many Linux
distributions' packaging system. This can be used to keep any user's process
from using too much CPU cycles. You can configure it accoring to `these
instructions <http://ubuntuforums.org/showthread.php?t=992706>`_ .

Shadow group (FreeBSD)
**********************

**NOTE:** This has not been tested and may not work as expected.

.. code-block:: bash

    ls -l /etc/spwd.db /etc/master.passwd
    -rw-------  1 root  wheel   2516 Aug 22 13:35 /etc/master.passwd
    -rw-------  1 root  wheel  40960 Aug 22 13:35 /etc/spwd.db


Add a shadow group if there isn't one, and make the shadow file group-readable:

.. code-block:: bash

    $ sudo pw group add shadow
    $ sudo chgrp shadow /etc/spwd.db
    $ sudo chmod g+r /etc/spwd.db
    $ sudo chgrp shadow /etc/master.passwd
    $ sudo chmod g+r /etc/master.passwd


We want our new user to be able to read the shadow passwords, so add it to the
shadow group:

.. code-block:: bash

    $ sudo pw user mod rhea -G shadow

Test that PAM works
-------------------

We can verify that PAM is working, with:

.. code-block:: bash

    $ sudo -u rhea python3 -c "import pamela, getpass; print(pamela.authenticate('$USER', getpass.getpass()))"
    Password: [enter your unix password]


Make a directory for JupyterHub
-------------------------------

JupyterHub stores its state in a database, so it needs write access to a directory.
The simplest way to deal with this is to make a directory owned by your Hub user,
and use that as the CWD when launching the server.

.. code-block:: bash

    $ sudo mkdir /etc/jupyterhub
    $ sudo chown rhea /etc/jupyterhub


Start jupyterhub
----------------

Finally, start the server as our newly configured user, `rhea`:

.. code-block:: bash

    $ cd /etc/jupyterhub
    $ sudo -u rhea jupyterhub --JupyterHub.spawner_class=sudospawner.SudoSpawner


And try logging in.

Troubleshooting: SELinux
------------------------

If you still get a generic `Permission denied` `PermissionError`, it's possible SELinux is blocking you.
Here's how you can make a module to allow this.
First, put this in a file named `sudo_exec_selinux.te`:

.. code-block:: bash

    module sudo_exec_selinux 1.1;

    require {
            type unconfined_t;
            type sudo_exec_t;
            class file { read entrypoint };
    }

    #============= unconfined_t ==============
    allow unconfined_t sudo_exec_t:file entrypoint;


Then run all of these commands as root:

.. code-block:: bash

    $ checkmodule -M -m -o sudo_exec_selinux.mod sudo_exec_selinux.te
    $ semodule_package -o sudo_exec_selinux.pp -m sudo_exec_selinux.mod
    $ semodule -i sudo_exec_selinux.pp


Troubleshooting: PAM session errors
-----------------------------------

If the PAM authentication doesn't work and you see errors for
`login:session-auth`, or similar, considering updating to a more recent version
of jupyterhub and disabling the opening of PAM sessions with
`c.PAMAuthenticator.open_sessions=False`.
