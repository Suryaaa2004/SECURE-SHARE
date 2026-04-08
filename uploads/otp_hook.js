Java.perform(function () {

    var Buffer = Java.use("okio.Buffer");
    var Charset = Java.use("java.nio.charset.Charset");
    var OkHttpClient = Java.use("okhttp3.OkHttpClient");

    OkHttpClient.newCall.overload("okhttp3.Request").implementation = function (request) {

        try {
            console.log("\n================ OTP REQUEST =================");
            console.log("URL      :", request.url().toString());
            console.log("METHOD   :", request.method());
            console.log("HEADERS  :\n" + request.headers().toString());

            var body = request.body();
            if (body !== null) {
                var buffer = Buffer.$new();
                body.writeTo(buffer);
                var charset = Charset.forName("UTF-8");
                var bodyString = buffer.readString(charset);
                console.log("BODY     :\n" + bodyString);
            } else {
                console.log("BODY     : <empty>");
            }

            console.log("=============================================\n");
        } catch (err) {
            console.log("[-] Error reading request:", err);
        }

        return this.newCall(request);
    };
});
