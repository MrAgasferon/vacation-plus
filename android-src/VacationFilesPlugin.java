package io.github.mragasferon.vacationplus.preview;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

@CapacitorPlugin(name = "VacationFiles")
public class VacationFilesPlugin extends Plugin {
    private static final int LIMIT = 2 * 1024 * 1024;

    @PluginMethod
    public void saveBackup(PluginCall call) {
        String name = call.getString("filename");
        String contents = call.getString("contents");
        if (name == null || !name.matches("[a-zA-Z0-9_-]+\\.json") || contents == null || contents.getBytes(StandardCharsets.UTF_8).length > LIMIT) {
            call.reject("Некорректный файл или размер превышает 2 МБ"); return;
        }
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/json");
        intent.putExtra(Intent.EXTRA_TITLE, name);
        try { startActivityForResult(call, intent, "saveResult"); }
        catch (Exception ex) { call.reject("Системное сохранение недоступно", ex); }
    }

    @ActivityCallback
    private void saveResult(PluginCall call, ActivityResult result) {
        if (call == null) return;
        Uri uri = selected(call, result); if (uri == null) return;
        new Thread(() -> {
            try (OutputStream out = getContext().getContentResolver().openOutputStream(uri, "wt")) {
                if (out == null) throw new java.io.IOException("Нет доступа к файлу");
                out.write(call.getString("contents").getBytes(StandardCharsets.UTF_8));
                out.flush();
            } catch (Exception ex) { call.reject("Не удалось записать JSON", ex); return; }
            JSObject response = new JSObject(); response.put("cancelled", false); call.resolve(response);
        }).start();
    }

    @PluginMethod
    public void openBackup(PluginCall call) {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        // Some file providers label JSON as text/plain or octet-stream. Content is validated in the calculator.
        intent.setType("*/*");
        try { startActivityForResult(call, intent, "openResult"); }
        catch (Exception ex) { call.reject("Системный выбор файла недоступен", ex); }
    }

    @ActivityCallback
    private void openResult(PluginCall call, ActivityResult result) {
        if (call == null) return;
        Uri uri = selected(call, result); if (uri == null) return;
        new Thread(() -> {
            try (InputStream in = getContext().getContentResolver().openInputStream(uri);
                 ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
                if (in == null) throw new java.io.IOException("Нет доступа к файлу");
                byte[] buffer = new byte[8192]; int n;
                while ((n = in.read(buffer)) != -1) {
                    if (bytes.size() + n > LIMIT) throw new java.io.IOException("Файл превышает 2 МБ");
                    bytes.write(buffer, 0, n);
                }
                String contents = new String(bytes.toByteArray(), StandardCharsets.UTF_8);
                if (contents.startsWith("\uFEFF")) contents = contents.substring(1);
                JSObject response = new JSObject(); response.put("cancelled", false); response.put("contents", contents); call.resolve(response);
            } catch (Exception ex) { call.reject("Не удалось прочитать JSON: " + ex.getMessage(), ex); }
        }).start();
    }

    private Uri selected(PluginCall call, ActivityResult result) {
        if (result.getResultCode() != Activity.RESULT_OK) {
            JSObject response = new JSObject(); response.put("cancelled", true); call.resolve(response); return null;
        }
        Uri uri = result.getData() == null ? null : result.getData().getData();
        if (uri == null || !"content".equals(uri.getScheme())) { call.reject("Нет доступа к выбранному документу"); return null; }
        return uri;
    }
}
