About This Document
===================

This document was created November 2021 as part of a `Trusted CI engagement <https://blog.trustedci.org/2021/08/engagement-with-jupyter.html>`_ .
The intent was to review existing documentation for single-server JupyterHub
deployments with a focus on security-related instructions, and suggest modifications
and additions to help users secure their Jupyter deployment on a single-server system.
These instructions should not be confused with documentation for `The Littlest
JupyterHub <https://tljh.jupyter.org>`_ .

.. important:: When configuring your JupyterHub installation, consider these two most important steps for better security: SSL/TLS encryption and external user accounts.

1. Enabling TLS/SSL (i.e., ``https://``) will encrypt all traffic between the JupyterHub
   server and remote web browsers. This will prevent a malicious user from snooping
   on the communication channel to discover secrets. See "Enabling Encryption" below.
2. Using external authentication allows you to leverage existing user accounts so you
   do not need to store passwords locally. There are several types of external user
   authenticators to choose from, including
   `OAuth2 <https://oauthenticator.readthedocs.io>`_ ,
   `LDAP <https://github.com/jupyterhub/ldapauthenticator>`_ , and
   `Kerberos <https://jupyterhub-kerberosauthenticator.readthedocs.io>`_ .  See "Use OAuthenticator.." below.

These are both covered in more detail below.

Applicable Jupyter Notebook Security Settings
=============================================

Many of the security settings for individual notebooks are also applicable for JupyterHub.  In particular, the information about what makes a notebook trusted or untrusted may be of use.  See the `Security in Notebook Documents <https://github.com/trustedci/jupyter-security-docs/blob/main/Notebook.rst>`_ page for more information.

General Security Practices
=============================

Before installing Jupyter, evaluate your server for general security concerns and take steps to "harden" your server. `NIST SP 800-123 <https://csrc.nist.gov/publications/detail/sp/800-123/final>`_ "Guide to General Server Security" outlines a comprehensive approach to evaluating vulnerabilities which may affect your server and steps you should take to protect your system against threats. Guides for hardening your Linux server, such as `this one <https://github.com/imthenachoman/How-To-Secure-A-Linux-Server>`_ can help you get started.

.. note:: The section below originates from `Security Overview - JupyterHub <https://jupyterhub.readthedocs.io/en/stable/reference/websecurity.html>`_.

Security audits
---------------

We recommend that you do periodic reviews of your deployment's security. It's
good practice to keep JupyterHub, configurable-http-proxy, and nodejs
versions up to date.

A handy website for testing your deployment is
`Qualsys' SSL analyzer tool <https://www.ssllabs.com/ssltest/analyze.html>`_ .

Authentication and Users
========================

Careful attention must be paid to which users are allowed to log in, the method used for them to log in, and what these users are allowed to do.  These are outlined in detail in the sections below.

Default Settings and User Basics
------------------------------

.. note:: The section below originates from `Authentication and User Basics - JupyterHub <https://jupyterhub.readthedocs.io/en/latest/getting-started/authenticators-users-basics.html>`_.

The default authenticator uses `PAM <https://en.wikipedia.org/wiki/Pluggable_authentication_module>`_ to authenticate system users with
their username and password. With the default authenticator, any user
with an account and password on the system will be allowed to log in to Jupyter. Creating new user accounts on Jupyter is accomplished by creating new users on the system.

.. note:: The section below originates from `Technical Overview - JupyterHub <https://jupyterhub.readthedocs.io/en/stable/reference/technical-overview.html>`_.

When JupyterHub starts, it will write to the ``jupyterhub.sqlite`` file in the current working directory, using settings
- including settings about users - from the configuration file.  The location of this database file can be changed by
updating ``c.JupyterHub.db_url`` in the configuration.  It's recommended to store it in either ``/etc/jupyterhub`` or ``/srv/jupyterhub``.

``jupyterhub.sqlite`` contains all of the state of the
Hub. This file allows the Hub to remember which users are running and
where, as well as storing other information enabling you to restart parts of
JupyterHub separately.   It also serves as the running authoritative source for user accounts and user sets
(e.g. ``allowed_users`` or ``admin_users``, which are explored in later sections), though the latter are
initially populated through configuration file settings if they've been added there.

Configuring and Limiting User Access
------------------------------------

Jupyter uses the concept of sets to control user access.  These are initially read from the configuration file when the ``jupyterhub.sqlite`` database is first created, and then may be modified afterward through the Hub’s admin panel or REST API.  They include:

- allowed_users
- blocked_users
- allowed_groups
- admin_users
- admin_groups

These are explored in more detail below.

Allowed and Blocked Users
*************************

.. note:: The section below originates from `Authentication and User Basics - JupyterHub <https://jupyterhub.readthedocs.io/en/latest/getting-started/authenticators-users-basics.html>`_.

Rather than allowing all system users to log into Jupyter, you can restrict which users are allowed to login by configuring a set,
``Authenticator.allowed_users``:

.. code-block:: python

    c.Authenticator.allowed_users = {'mal', 'zoe', 'inara', 'kaylee'}

Alternatively, specific users can be denied access to by updating the ``Authenticator.blocked_users`` set:

.. code-block:: python

    c.Authenticator.blocked_users = {'jane'}

Users in the ``allowed_users`` set are added to the Hub database when the configuration file is read at time the Hub is
started.  Because of this, after the Hub has been started with a configuration allowing a particular user, removing that user from the configuration file is no longer sufficient to terminate their access.  The user must be removed using the process below.

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

Administrative Users
----------------------

.. note:: The section below originates from `Authentication and User Basics - JupyterHub <https://jupyterhub.readthedocs.io/en/latest/getting-started/authenticators-users-basics.html>`_.

.. note::

    As of JupyterHub 2.0, more granular options than the full permissions of ``admin_users``     can be configured. Instead, `roles
    <https://jupyterhub.readthedocs.io/en/latest/rbac/roles.html>`_ can be assigned to users or
    groups with only the scopes they require.

Admin users of JupyterHub, members of the set ``admin_users``, can add and remove users from
the user ``allowed_users`` set. ``admin_users`` can also take actions on other users'
behalf, such as stopping and restarting their servers.

A set of initial admin users, ``admin_users`` can be configured as follows:

.. code-block:: python

    c.Authenticator.admin_users = {'mal', 'zoe'}

Users in the admin set are automatically added to the user ``allowed_users`` set,
if they are not already present.

Each authenticator may have different ways of determining whether a user is an
administrator. By default JupyterHub uses the PAMAuthenticator which provides the
``admin_groups`` option and can set administrator status based on a system-level user
group. For example we can set any user in the ``wheel`` group to have admin privileges:

.. code-block:: python

    c.PAMAuthenticator.admin_groups = {'wheel'}

Give admin access to other users' notebook servers (``admin_access``)
*******************************************************************

Using the default ``JupyterHub.admin_access`` setting of ``False``, admins
do not have permission to log in to single user notebook servers
owned by *other users*. If ``JupyterHub.admin_access`` is set to ``True``,
then admins have permission to log in *as other users* on their
respective machines, for debugging.

**As a courtesy, you should make sure your users know if admin_access is enabled.**  Additionally, especially great care should be taken ensuring that only trusted administrators are a member of the admin_users group.

Special Authenticator Setups
----------------------------

Use OAuthenticator to support OAuth with popular service providers
******************************************************************
Using external authentication is highly recommended, because it removes the risk involved with storing local passwords on the system.  Ideally it can also allow users to remember fewer passwords, if an identity provider already in use by the users can be leveraged for JupyterHub access as well.

JupyterHub's `OAuthenticator <https://github.com/jupyterhub/oauthenticator>`_ currently supports the following
popular services:

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

Use LocalAuthenticator to create system users
*********************************************

The ``LocalAuthenticator`` is a special kind of authenticator that has
the ability to manage users on the local system. When you try to add a
new user to the Hub, a ``LocalAuthenticator`` will check if the user
already exists. If the configuration value for ``create_system_users`` is set to true, , the LocalAuthenticator has
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
system's UNIX users.

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

.. note:: The section below originates from `Security settings - JupyterHub <https://jupyterhub.readthedocs.io/en/latest/getting-started/security-basics.html>`_.

Since JupyterHub includes authentication and allows arbitrary code execution,
you should not run it without TLS/SSL (HTTPS).

In order to secure all communication within the Jupyter server components and between Jupyter and the users, encryption needs to be configured in a number of places:

* Between the user and the server - either the Jupyter proxy or a web server frontend
* (If applicable) Between a web server frontend and Jupyter proxy
* Between the Jupyter proxy and Hub
* Between the Jupyter proxy and notebook server
* Between the Jupyter notebook server and the kernels

If all of the Jupyter components are contained on a single server, then all of the communication except the first bullet point happens internally to the server, making it less of a security risk than any external communication.  However, users on the system could still potentially sniff and observe that traffic, and so it should still be encrypted.

External Encryption
---------------------

First, a design decision must be made as to whether a dedicated web server will serve as the frontend for
JupyterHub or whether the proxy will be directly accessed.  It is highly recommended to run a web server
like Apache or Nginx, even though this means maintaining an additional service.  These dedicated web
servers are more carefully monitored and updated for any sorts of security or compatibility issues than
the Jupyter proxy, which is more intended for testing than as a production, widely accessed service.
Additionally, these allow for running multiple services on the same machine without needing to use
non-standard port numbers, and also more readily and easily interact with other tools like Let's Encrypt.

Encryption with a Web Server Frontend
*************************************
If using a web server frontend like Apache or Nginx, standard methods for using TLS/SSL for HTTPS should be followed.  Then, the web server should be configured to direct requests to a given URL to the Jupyter proxy.  An example for Apache is given below.

.. code-block:: Apache

  <VirtualHost *:80>
  ServerName example.org
  Redirect / https://example.org/
  </VirtualHost>
  <VirtualHost *:443>
  ServerName example.org

  SSLCertificateFile /etc/letsencrypt/live/example.org/fullchain.pem
  SSLCertificateKeyFile /etc/letsencrypt/live/example.org/privkey.pem
  Include /etc/letsencrypt/options-ssl-apache.conf

  RewriteEngine On
  RewriteCond %{HTTP:Connection} Upgrade [NC]
  RewriteCond %{HTTP:Upgrade} websocket [NC]

  RewriteRule /jhub/(.*) ws://127.0.0.1:8000/jhub/$1 [P,L]
  RewriteRule /jhub/(.*) http://127.0.0.1:8000/jhub/$1 [P,L]

  <Location "/jhub/">
    # preserve Host header to avoid cross-origin problems
    ProxyPreserveHost on
    # proxy to JupyterHub
    ProxyPass         http://127.0.0.1:8000/jhub/
    ProxyPassReverse  http://127.0.0.1:8000/jhub/
  </Location>
</VirtualHost>

This will secure communication between clients and the server.  Communication between the web server frontend and Jupyter proxy also needs to be encrypted.


Encryption with Direct Jupyter Proxy Access
*******************************************

Although not recommended, the Proxy can also be directly accessed and encryption can happen directly on the proxy.

.. note:: The section below originates from `Technical Overview - JupyterHub <https://jupyterhub.readthedocs.io/en/stable/reference/technical-overview.html>`_.

By default, the Proxy listens on all public interfaces on port 8000.
Thus you can reach JupyterHub through either:

- ``http://localhost:8000``
- or any other public IP or domain pointing to your system.

.. note:: The section below originates from `Security settings - JupyterHub <https://jupyterhub.readthedocs.io/en/latest/getting-started/security-basics.html>`_.


Jupyter can be configured to encrypt this traffic by providing a certificate. This will require you to obtain an official, trusted SSL certificate or create a
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

It is also possible to use `Let’s Encrypt  <https://letsencrypt.org/>`_ to obtain
a free, trusted SSL certificate. If you run Let’s Encrypt using the default
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

Internal Encryption
-------------------
The default settings require several changes in order to encrypt all communications internal to Jupyter components.

.. note:: The section below originates from `Security Overview - JupyterHub <https://jupyterhub.readthedocs.io/en/stable/reference/websecurity.html>`_.

Encrypt internal connections with SSL/TLS
*****************************************

By default, all communication on the server between the proxy, hub, and single
-user notebooks happens unencrypted. Setting the `internal_ssl` flag in
`jupyterhub_config.py` secures these communications.  With this setting enabled, JupyterHub will create an internal certificate authority and automatically sign certificates for notebooks on demand as they are created.  This setting requires that the enabled spawner can use the certificates
generated by the Hub.  The default LocalProcessSpawner can do this, so this concern is only applicable when using non-default settings..

.. note:: The section below originates from `Spawners - JupyterHub <https://jupyterhub.readthedocs.io/en/stable/reference/spawners.html>`_.

For a custom spawner to
utilize these certs, there are two methods of interest on the base `Spawner`
class: `.create_certs` and `.move_certs`.

The first method, `.create_certs` will sign a key-cert pair using an internally
trusted authority for notebooks.

If needed, an `alt_names` kwarg can be passed to apply ip and dns name to the certificate.This is used for certificate authentication (verification). Without proper
verification, the notebook will be unable to communicate with the Hub and
vice versa when `internal_ssl` is enabled. For example, given a deployment
using the `DockerSpawner` which will start containers with ips from the
docker subnet pool, the `DockerSpawner` would need to instead choose a
container ip prior to starting and pass that to `.create_certs`. In general though, this method will not need to be changed and the default
ip/dns (localhost) info will suffice.

When `.create_certs` is run, it will create certificates in a default, central
location specified by the `c.JupyterHub.internal_certs_location` setting. For spawners
that need access to these certs elsewhere (i.e. on another host altogether),
the `.move_certs` method can be overridden to move the certs appropriately.
Again, using `DockerSpawner` as an example, this would entail moving certs
to a directory that will get mounted into the container this spawner starts.

Encrypt Notebook Communication
******************************

.. note:: The section below originates from `Security Overview - JupyterHub <https://jupyterhub.readthedocs.io/en/stable/reference/websecurity.html>`_.

It is also important to note that the internal encryption provided by the `internal_ssl` setting **does not** cover the
communication between the notebook client and kernel. ZeroMQ TCP (zmq tcp) sockets are used for communication between the notebook client and kernel, utilizing a random high port allocated when the notebook starts up. This port can be identified by looking at the iopub value in the .local/share/jupyter/runtime/kernel-*.json file.

While users cannot
submit arbitrary commands to another user's kernel, they can bind to these
sockets and listen. This eavesdropping can be
mitigated by setting `KernelManager.transport` setting to `ipc`, which applies standard
Unix permissions to the communication sockets, thereby restricting
communication to the socket owner.

Other Jupyter Encryption and Authentication Settings
====================================================

Jupyter automatically handles communication between the Hub and Proxy through an automatically generated authentication secret or token.  However, manually specifying one removes the need to restart the Proxy if the Hub restarts.

Likewise, an encryption secret is automatically generated to handle encryption of cookies handed out to
clients' browsers.  Manually specifying this as well means that single user notebook servers no longer need to be restarted if the Hub is restarted.

Proxy authentication token
--------------------------

.. note:: The section below originates from `Security settings - JupyterHub <https://jupyterhub.readthedocs.io/en/latest/getting-started/security-basics.html>`_.

Using the default ``ConfigurableHTTPProxy`` implementation, the Hub authenticates its requests to the Proxy using a secret token that
the Hub and Proxy agree upon.
If a secret token is not manually set, one will be automatically generated each time the Hub restarts.  This means that the proxy must also be restarted each time the Hub restarts - although this occurs anyway in the default configuration since the Proxy is a subprocess of the Hub.

The value of this token should be a random string (for example, generated by
``openssl rand -hex 32``). You can store it in the configuration file or as an
environment variable.

.. note::

  Not all proxy implementations use an auth token.

Setting the value in the configuration file ``jupyterhub_config.py`` uses the ConfigurableHTTPProxy.api_token option:

.. code-block:: python

    c.ConfigurableHTTPProxy.api_token = 'abc123...' # any random string

The value of the proxy authentication token can also be made accessible to the Hub and Proxy
using the ``CONFIGPROXY_AUTH_TOKEN`` environment variable:

.. code-block:: bash

    export CONFIGPROXY_AUTH_TOKEN=$(openssl rand -hex 32)

The environmental variable needs to be available to the service accounts running the Hub and the Proxy services.  This is generally the root account unless JupyterHub is run without root privileges.  It should not be available for user accounts on the system.

Cookie secret
-------------

.. note:: The section below originates from `Security settings - JupyterHub <https://jupyterhub.readthedocs.io/en/latest/getting-started/security-basics.html>`_.

The cookie secret is an encryption key used to encrypt the browser cookies
which are used for authentication. Three common methods are described for
generating and configuring the cookie secret.

If the cookie secret file doesn't exist when the Hub starts, a new cookie
secret is generated and stored. The file must not be readable by
``group`` or ``other`` or the server won't start. The recommended permissions
for the cookie secret file are ``600`` (owner-only rw).

Additionally, if the secret changes when the Hub restarts (due to one not being specified in the configuration file, or an environmental variable being dynamically generated), all users will be logged out of their notebooks when the Hub process restarts.

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

If you would like to avoid the need for files, the value can be loaded in the
Hub process from the ``JPY_COOKIE_SECRET`` environment variable, which is a
hex-encoded string. You can set it this way:

.. code-block:: bash

    export JPY_COOKIE_SECRET=$(openssl rand -hex 32)

For security reasons, this environment variable should only be visible to the
Hub. If you set it dynamically as above, all users will be logged out each time
the Hub starts.

You can also set the cookie secret in the configuration file
itself, ``jupyterhub_config.py``, as a binary string:

.. code-block:: python

    c.JupyterHub.cookie_secret = bytes.fromhex('64 CHAR HEX STRING')

.. important::

   If the cookie secret value changes for the Hub, all single-user notebook
   servers must also be restarted.

Protecting Users
================

.. note:: The section below originates from `Security Overview - JupyterHub <https://jupyterhub.readthedocs.io/en/stable/reference/websecurity.html>`_.

Semi-trusted and untrusted users
-----------------------------------

JupyterHub is designed to be a *simple multi-user server for modestly sized
groups* of **semi-trusted** users. This means that additional configuration must be done by the administrator in order to secure JupyterHub for **untrusted** users. Much care is required to secure a Hub, with extra caution on
protecting users from each other if the Hub is serving untrusted users.

From a high level, to fully protect all users from each other, JupyterHub administrators must take steps on their server to ensure that:

- Cross-site protections are in effect among notebooks and between the notebooks and the Hub through the use of subdomains
- A user **does not have permission** to modify their single-user notebook server,
  including:
   - A user **may not** install new packages in the Python environment that runs their single-user server.
   - If the ``PATH`` is used to resolve the single-user executable (instead of using an absolute path), a user **may not** create new files in any ``PATH`` directory that precedes the directory containing ``jupyterhub-singleuser``.
   - A user may not modify environment variables (e.g. PATH, PYTHONPATH) for their single-user server.
- A user **may not** modify the configuration of the notebook server (the ``~/.jupyter`` or ``JUPYTER_CONFIG_DIR`` directory).

These steps are covered in more detail below.

Additionally, if any additional services are run on the same domain as the Hub, the services
**must never** display user-authored HTML that is neither *sanitized* nor *sandboxed*
(e.g. IFramed) to someone other than the owner/creator of that file, as determined by their authentication.

Mitigating security issues
---------------------------

Several approaches to mitigating these issues with configuration
options provided by JupyterHub include:

Enable subdomains
*****************

One aspect of JupyterHub's *design simplicity* for **semi-trusted** users is that
the Hub and single-user servers are placed in a *single domain*, behind a
`proxy <https://github.com/jupyterhub/configurable-http-proxy>`_. By default, single-user servers are
accessed at ``http://.../jhub/user/<username>/``.

However, if the Hub is serving untrusted
users, this becomes a challenge.  With a single domain, many of the web's cross-site protections (i.e. against cross site scripting and cross site request forgery) are not applied between
single-user servers and the Hub, or between single-user servers and each
other.  This is because browsers see the whole thing (proxy, Hub, and single user
servers) as a single website (i.e. single domain).

This limitation can be overcome by running single-user servers on their own subdomains, an ability that JupyterHub supports.
Each user's single-user notebook server will be accessible at ``username.jupyter.example.org``, and cross origin protections between these different domains have the desired effect of protecting user servers and the Hub from each other. This also
requires all user subdomains to point to the same IP address, which is most easily
accomplished with wildcard DNS.

Since this spreads the service across multiple
domains, you will need wildcard SSL, as well. Unfortunately, for many
institutional domains, wildcard DNS and SSL are not available, and this may pose a potential challenge.

Spawner Security
****************

Default Spawner Security Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unless configured with an alternate spawner, JupyterHub uses the LocalProcessSpawner to create the
single-user notebook servers.  This is configured with ``c.JupyterHub.spawner_class
= jupyterhub.spawner.LocalProcessSpawner``.  Additionally, the default spawning command is configured with ``c.Spawner.cmd = ['jupyterhub-singleuser']``.

The default settings prevent the notebook server from using any configuration files found in the user's
$HOME directory, per the c.Spawner.disable_user_config setting.  However, the default settings for the single-user
notebook server process will still use any Python packages installed under ``$HOME/.local`` by the user.
As long as the host operating system is configured to not allow users to install python packages on a
system-wide level, which is true by default in most modern Linux operating systems, if a user for
instance spawns a bash shell using ``subprocess.Popen`` and uses pip to install a package, it will be
available to their notebook server(s) but not others'.  As long as they can only impact their own
notebooks, this is not an issue.

Security Settings for Spawners
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Disable user config
^^^^^^^^^^^^^^^^^^^

JupyterHub provides a
The configuration option ``Spawner.disable_user_config`` can be set to prevent
any user-owned configuration files from being loaded within JupyterHub.

Prevent spawners from evaluating shell configuration files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For most spawners, ``PATH`` is not something users can influence, but care should
be taken to ensure that the spawner does _not_ evaluate shell configuration
files prior to launching the server.  This is specific to the implementation of the spawner.

Isolate packages using virtualenv
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The environment in which the single-user server runs should be protected from user modification.  Although most modern Linux operating systems prevent users without root privileges from being able to install python packages into a system-wide level, this is still most safely and easily accomplished by running the single-user server in a virtualenv with disabled system-site-packages.  Users should not have permission to install packages into this environment.

Please note, this is separate from users installing additional packages into the environment(s) where the user's kernel(s) run.  User modification here does not pose additional risk to the security of the web application itself.

Running JupyterHub without Root Privileges
==============================================

.. note:: The section below originates from `Run JupyterHub without root privileges using sudo <https://jupyterhub.readthedocs.io/en/stable/reference/config-sudo.html>`_.

.. important:: Running JupyterHub without root privileges is the most secure option.  However, setting up ``sudo`` permissions involves many pieces of system configuration. It can be easy to do incorrectly by missing a step and then becomes difficult to debug.  These two factors should be weighted against each other when making a decision on whether to choose this route.

Since JupyterHub needs to spawn processes as other users, the simplest way
is to run it as root, spawning user servers with `setuid <http://linux.die.net/man/2/setuid>`_.
But this isn't especially safe, because you have a process running on the
public web as root.

A **more prudent way** to run the server while preserving functionality is to
create a dedicated user with ``sudo`` access restricted to launching and
monitoring single-user servers.

This document describes how to get the full default behavior of JupyterHub while running notebook servers as real system users on a shared system without running the Hub itself as root.  It also details how to maintain full spawner functionality even for those spawners (unlike DockerSpawner or OAuthenticator) that require elevated permissions.

Create a user
-------------

To do this, first create a user that will run the Hub:

.. code-block:: bash

 sudo useradd jupyter

This user shouldn't have a login shell or password.  Depending on the system, setting this at the command line may be possible with -r), or `/etc/password` may need to be edited.

Set up sudospawner
------------------

Next, you will need `sudospawner <https://github.com/jupyter/sudospawner>`_
to enable monitoring the single-user servers with sudo:

.. code-block:: bash

 sudo python3 -m pip install sudospawner

Now we have to configure sudo to allow the Hub user (``jupyter``) to launch
the sudospawner script on behalf of our hub users (here ``zoe`` and ``wash``).
We want to confine these permissions to only what we really need.

Edit ``/etc/sudoers``
------------------

To do this we add to ``/etc/sudoers`` (use ``visudo`` for safe editing of sudoers):

- specify the list of users ``JUPYTER_USERS`` for whom ``jupyter`` can spawn servers
- set the command ``JUPYTER_CMD`` that ``jupyer`` can execute on behalf of users
- give ``jupyter`` permission to run ``JUPYTER_CMD`` on behalf of ``JUPYTER_USERS``
  without entering a password

For example:

.. code-block:: bash

  # comma-separated list of users that can spawn single-user servers
  # this should include all of your Hub users
  Runas_Alias JUPYTER_USERS = jupyter, zoe, wash

  # the command(s) the Hub can run on behalf of the above users without needing a password
  # the exact path may differ, depending on how sudospawner was installed
  Cmnd_Alias JUPYTER_CMD = /usr/local/bin/sudospawner

  # actually give the Hub user permission to run the above command on behalf
  # of the above users without prompting for a password
  jupyter ALL=(JUPYTER_USERS) NOPASSWD:JUPYTER_CMD

It might be useful to modify ``secure_path`` to add commands in path.

As an alternative to adding every user to the ``/etc/sudoers`` file, you can
use a group in the last line above, instead of ``JUPYTER_USERS``:

.. code-block:: bash

  jupyter ALL=(%jupyterhub) NOPASSWD:JUPYTER_CMD

If the ``jupyterhub`` group exists, there will be no need to edit ``/etc/sudoers``
again. A new user will gain access to the application when added to the group:

.. code-block:: bash

  $ adduser -G jupyterhub newuser

Test ``sudo`` setup
-----------------

Test that the new user doesn't need to enter a password to run the sudospawner
command.

This should prompt for your password to switch to jupyter, but *not* prompt for
any password for the second switch. It should show some help output about
logging options:

.. code-block:: bash

  $ sudo -u jupyter sudo -n -u $USER /usr/local/bin/sudospawner --help
  Usage: /usr/local/bin/sudospawner [OPTIONS]

  Options:

  --help          show this help information
  ...

And this should fail:

.. code-block:: bash

  $ sudo -u jupyter sudo -n -u $USER echo 'fail'
  sudo: a password is required

Enable PAM for non-root
-----------------------

By default, `PAM authentication <http://en.wikipedia.org/wiki/Pluggable_authentication_module>`_
is used by JupyterHub. To use PAM, the process may need to be able to read
the shadow password database.

Shadow group (Linux)
********************

.. note::

  On Fedora based distributions there is no clear way to configure the PAM database to allow sufficient access for authenticating with the target user's password from JupyterHub. As a workaround we recommend use an   `alternative authentication method <https://github.com/jupyterhub/jupyterhub/wiki/Authenticators>`_ .

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

    $ sudo usermod -a -G shadow jupyter

If you want JupyterHub to serve pages on a restricted port (such as port 80 for http),
then you will need to give ``node`` permission to do so:

.. code-block:: bash

  sudo setcap 'cap_net_bind_service=+ep' /usr/bin/node

However, you may want to further understand the consequences of this.

You may also be interested in limiting the amount of CPU any process can use
on your server. ``cpulimit`` is a useful tool that is available for many Linux
distributions' packaging system. This can be used to keep any user's process
from using too much CPU cycles. You can configure it according to `these
instructions <http://ubuntuforums.org/showthread.php?t=992706>`_.

Shadow group (FreeBSD)
**********************

..note::

  This has not been tested and may not work as expected.

.. code-block:: bash

  $ ls -l /etc/spwd.db /etc/master.passwd
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

  $ sudo pw user mod jupyter -G shadow

Test that PAM works
-------------------

We can verify that PAM is working, with:

.. code-block:: bash

  $ sudo -u jupyter python3 -c "import pamela, getpass; print(pamela.authenticate('$USER', getpass.getpass()))"
  Password: [enter your unix password]

Make a directory for JupyterHub
-------------------------------

JupyterHub stores its state in a database, so it needs write access to a directory.
The simplest way to deal with this is to make a directory owned by your Hub user,
and use that as the CWD when launching the server.

.. code-block:: bash

  $ sudo mkdir /etc/jupyterhub
  $ sudo chown jupyter /etc/jupyterhub

Start jupyterhub
-----------------

Finally, start the server as our newly configured user, ``jupyter``:

.. code-block:: bash

  $ cd /etc/jupyterhub
  $ sudo -u jupyter jupyterhub --JupyterHub.spawner_class=sudospawner.SudoSpawner


And try logging in.

Troubleshooting: SELinux
------------------------

If you still get a generic ``Permission denied PermissionError``, it's possible SELinux is blocking you.  
Here's how you can make a module to allow this.
First, put this in a file named ``sudo_exec_selinux.te``:

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
``login:session-auth``, or similar, considering updating to a more recent version
of JupyterHub and disabling the opening of PAM sessions with
``c.PAMAuthenticator.open_sessions=False``.

Vulnerability Reporting
=======================

.. note:: The section below originates from `Security Overview - JupyterHub <https://jupyterhub.readthedocs.io/en/stable/reference/websecurity.html>`_.

If you believe you've found a security vulnerability in JupyterHub, or any
Jupyter project, please visit `https://jupyter.org/security <https://jupyter.org/security>`_ for information on how to report it.
