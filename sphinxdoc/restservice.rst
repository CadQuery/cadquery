.. _buildservice:

******************************************
The Parametric Parts Build Service
******************************************


If you have registered for an account, you can use the REST api to build models from your website or platform.
Each request to the service will construct a model in the format you choose.


Using the Build Service
-------------------------

The Build Service endpoint is  `<https://parametricparts.com/parts/build>`_

In each request, you provide four  main things via either a GET or a POST :

    1.  **An API Key**, to identify yourself.
    2.  **A ModelScript to build**, either by providing the entire script, or the id of a model stored on
        parametricparts.com,
    3.  **The type of output** you want,
    4.  **The Model parameters**  that should be supplied to the model.

.. note::

    GET or POSTs are allowed, but be aware that URLs for GET requests are limited to 4K,
    so POSTs are advised if you are sending your modelScript via the URL

The output streamed in the format you have requested.

Errors are provided using standard HTTP error codes:

    :200: if the build is a success
    :403: if the APIKey is invalid, or if your account cannot execute any more downloads
    :404: if the requested model  cannot be found
    :50X: if there is a problem generating the model

Build Service Parameters
--------------------------

All parameters must be URL encoded:

    :key:
        (Required) Your API Key. See :ref:`gettingakey` If you do not have one.

    :id:
        (Either id or s is Required) The id of the ParametricParts.com ModelScript to build.  The id is the last part of the url
        when viewing the model:  http://parametricparts.com/parts/<modelId>.  Model ids are between 7 and 9
        characters, for example '4hskpb69'.

    :s:
        (Either id or s is Required) The ModelScript to build. This should be a valid parametricparts.com ModelScript.
        If both id and s are provided, s takes precedence.

    :type:
        (Required) ("STL" | "STEP" | "AMF" | "TJS" ). The type of output you want to receive. STL, STEP,
        and AMF return the corresponding industry standard format.
        TJS will return JSON content suitable for display in a Three.js scene.

    :preset:
        (Optional) The name of a preset defined in the ModelScript. If omitted, other parameters are used.
        If a preset is provided in addition to parameters, then the preset is applied first, and then
        parameters are set afterwards.

    :<params>:
        (Optional) Remaining URL parameters are mapped onto ModelScript parameters of the same name. Each
        parameter value must have the datatype corresponding to the parameter in the ModelScript. To supply multiple
        parameters, send an HTTP parameter for each desired value, having name matching the name of the ModelScript
        parameter, and value having the value for that parameter.  If no
        parameters are provided, output is generated using ModelScript defaults.

Example
--------------------------

This example builds STEP for a trivial model, without supplying any model parameters or presets::

    POST https://parametricparts.com/parts/build HTTP/1.1
    key:259cd575c9a2998420ac65f21b2d6b2a
    s:def+build%28%29%3A%0D%0A++++return+Part.makeBox%281%2C2%2C3%29%0D%0A++++++++
    type:AMF


This example selects an existing model (2qus7a32 ) on the server, and requests
preset 'short', as well as adjusting parameter 'p_length' to value 120::

    POST https://parametricparts.com/parts/build HTTP/1.1
    key:259cd575c9a2998420ac65f21b2d6b2a
    id:2qus7a32
    type:STL
    preset:short
    p_length:120


.. _gettingakey:

Signing Up
-----------------------

In order to use the API, you first need to have an API key. To get one:

   1.  `Sign Up <https://parametricparts.com/account/signup>`_ for a ParametricParts account
   2.  `Contact ParametricParts Support <http://support.parametricparts.com/customer/portal/emails/new>`_ to request API key access.
       API keys usually require an enterprise license, but are available for free evaluation if you request access
   3.  Log onto your ParametricParts account, and generate an API Key using the `API Keys <https://localhost:8080/key/keys>`_ link.
   4.  Test your api key using the api key tester `Here <https://parametricparts.com/apitester>`_
       If the test goes well, you'll see STL output from the sample script.

Now you are ready to make REST requests to build models.

.. warning::

    Make sure to keep your API Key secret, as any requests that use your key will be charged to your account.
    You can disable or generate a new API Key from your account page.