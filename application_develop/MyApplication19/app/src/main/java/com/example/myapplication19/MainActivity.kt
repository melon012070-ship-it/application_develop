package com.example.myapplication19



import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import com.example.myapplication19.R
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.OnMapReadyCallback
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.GroundOverlayOptions
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.MarkerOptions
import com.google.android.gms.location.FusedLocationProviderClient
import androidx.activity.result.contract.ActivityResultContracts
import com.google.android.gms.maps.SupportMapFragment
import com.google.android.gms.location.LocationServices
import android.annotation.SuppressLint
import com.google.android.gms.maps.model.Marker



class  MainActivity : AppCompatActivity(),OnMapReadyCallback {
    lateinit var gMap:GoogleMap
    lateinit var fusedClient: FusedLocationProviderClient
    private var myMarker: Marker? = null




    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
            val fine = result[Manifest.permission.ACCESS_FINE_LOCATION] ?: false
            val coarse = result[Manifest.permission.ACCESS_COARSE_LOCATION] ?: false
            if (fine || coarse) {
                showMyLocationOnMap()
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        title="Google 지도 활용"
        fusedClient = LocationServices.getFusedLocationProviderClient(this)
        val mapFrag = supportFragmentManager.findFragmentById(R.id.map) as SupportMapFragment
        mapFrag.getMapAsync(this)


    }

    override fun onMapReady(map: GoogleMap) {
        gMap=map
        gMap.uiSettings.isZoomControlsEnabled=true

        checkAndRequestLocationPermission() //* 권한 확인 후 현재 위치 표시/이동/마커
    }
    private fun checkAndRequestLocationPermission(){
        val fineGranted=ContextCompat.checkSelfPermission(
            this,Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        val coarseGranted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED

        if(fineGranted || coarseGranted){

            showMyLocationOnMap()
        } else {
            permissionLauncher.launch(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION
                )
            )
        }


    }
    @SuppressLint("MissingPermission")
private fun showMyLocationOnMap() {
        // 파란 내 위치 점 표시(권한 필요)
        try {
            gMap.isMyLocationEnabled = true
        } catch (e: SecurityException) { }

        fusedClient.lastLocation.addOnSuccessListener { location ->
            if (location != null) {
                val myPos = LatLng(location.latitude, location.longitude)

                // 내 위치 마커(핀) 표시
                myMarker?.remove()
                myMarker = gMap.addMarker(
                    MarkerOptions()
                        .position(myPos)
                        .title("내 현재 위치")
                )


                // 내 위치로 자동 이동
                gMap.animateCamera(CameraUpdateFactory.newLatLngZoom(myPos, 16f))
            }  else {
            val yongin = LatLng(37.2411, 127.1775) // 용인(임시 기본값)
            myMarker?.remove()
            myMarker = gMap.addMarker(
                MarkerOptions()
                    .position(yongin)
                    .title("용인(기본 위치)")
            )
            gMap.animateCamera(CameraUpdateFactory.newLatLngZoom(yongin, 15f))
        }

    }
    }





}