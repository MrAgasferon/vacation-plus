package io.github.mragasferon.vacationplus;

import android.content.Intent;
import android.net.Uri;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "VacationUpdates")
public class VacationUpdatesPlugin extends Plugin {
    @PluginMethod
    public void openRelease(PluginCall call) {
        String tag = call.getString("tag");
        if (tag == null || !tag.matches("v(0|[1-9][0-9]{0,3})\\.(0|[1-9][0-9]{0,2})\\.(0|[1-9][0-9]{0,2})")) {
            call.reject("Некорректная версия"); return;
        }
        // No arbitrary URLs or installation permissions. Android/browser handles download and install.
        Uri uri = Uri.parse("https://github.com/MrAgasferon/vacation-plus/releases/tag/" + tag);
        try {
            getActivity().startActivity(new Intent(Intent.ACTION_VIEW, uri));
            call.resolve();
        } catch (Exception ex) { call.reject("Не удалось открыть браузер", ex); }
    }
}
