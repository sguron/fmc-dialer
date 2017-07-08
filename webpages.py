__author__ = 'TheArchitect'

class Pages(object):
    PAGE_FAQ = """
<html><head>
    <title>Free My Call - FAQ</title>
<style>
body{background:#f8f8f8;}
.hide-faq{display:none;}
</style>
{% JQUERY %}
<script type='text/javascript'>//<![CDATA[
$(function(){alert("This should work");
//jQuery("a.faq-click").click(function(event){jQuery(event.target).siblings("span").toggle(300); event.preventDefault();});
});//]]>
</script>
<!--saved from <url=about:internet>-->
</head>
<body>
<noscript>Scripts not running</noscript>
    <div id="body-wrap">
        <h1>FAQ</h1>
        <hr>
        <ul id="faq-ul">
            <li><span class="faq-click" >- How does it work ?</span>  <span class="faq-content hide-faq">Registration is a fast process. Make sure you enter all your details correctly on the signup form. Once done send us the form and your account will be created immediately if all details are correct.</span> </li>
            <li><a class="faq-click" href="#" onclick='jQuery(this).siblings("span").toggle(300); return false;'>- How does it work ?</a>  <span class="faq-content hide-faq">Registration is a fast process. Make sure you enter all your details correctly on the signup form. Once done send us the form and your account will be created immediately if all details are correct.</span> </li>
            <li><a class="faq-click" href="#">- How does it work ?</a>  <span class="faq-content hide-faq">Registration is a fast process. Make sure you enter all your details correctly on the signup form. Once done send us the form and your account will be created immediately if all details are correct.</span> </li>
        </ul>
    </div>
    <script type="text/javascript">jQuery("a.faq-click").click(function(event){jQuery(event.target).siblings("span").toggle(300); event.preventDefault();});</script>
</body></html>
"""

    PAGE_JSTESTS= """<html><head>{% JQUERY %}<script type='text/javascript'>alert($);</script></head><body><div id="hook">Script tester ;)</body></html> """
    PAGE_ADS= """<html><head></head><body><h1>Native Test</h1><hr><a href="app://onadclick">Ad click</a><br><a href="app://printarg?aaa,bbb">PrintArgs</a><br><a href="app://close">Close</a></html> """

    PAGE_TEST = """<h1>{% TEST %}</h1>"""
    pages = {
                "/dialer/faq.html" : PAGE_FAQ,
                "/test/test.html" : PAGE_TEST,
                "/js.html" : PAGE_JSTESTS,
                "/dialer/ads.html" : PAGE_ADS
            }