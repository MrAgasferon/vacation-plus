package io.github.mragasferon.vacationplus.preview;

import android.os.Bundle;
import androidx.activity.OnBackPressedCallback;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(VacationFilesPlugin.class);
        super.onCreate(savedInstanceState);
        // Register after Capacitor has created its bridge and loaded its plugins.
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (getBridge() != null && getBridge().getWebView() != null) {
                    getBridge().getWebView().evaluateJavascript(
                        "document.dispatchEvent(new Event('vacation-native-back'))", null);
                }
            }
        });
    }
}
